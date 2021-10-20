# -*- coding: utf-8 -*-
# Copyright © tandemdude 2020-present
#
# This file is part of Lightbulb.
#
# Lightbulb is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lightbulb is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Lightbulb. If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

__all__ = ["OptionLike", "CommandLike", "Command"]

import abc
import dataclasses
import inspect
import typing as t

import hikari

from lightbulb_v2 import errors

if t.TYPE_CHECKING:
    from lightbulb_v2 import checks
    from lightbulb_v2 import context as context_


@dataclasses.dataclass
class OptionLike:
    name: str
    description: str
    arg_type: t.Type[t.Any] = str
    required: t.Optional[bool] = None
    choices: t.Optional[t.Sequence[t.Union[str, int, float, hikari.CommandChoice]]] = None
    channel_types: t.Optional[t.Sequence[hikari.ChannelType]] = None
    default: hikari.UndefinedOr[t.Any] = hikari.UNDEFINED


@dataclasses.dataclass
class CommandLike:
    callback: t.Callable[[context_.base.Context], t.Coroutine[t.Any, t.Any, None]]
    name: str
    description: str
    options: t.MutableMapping[str, OptionLike] = dataclasses.field(default_factory=dict)
    checks: t.Sequence[checks.Check] = dataclasses.field(default_factory=list)
    cooldown_manager: t.Optional[...] = None  # TODO
    error_handler: t.Optional[t.Callable[[context_.base.Context], t.Coroutine[t.Any, t.Any, t.Optional[bool]]]] = None
    aliases: t.Sequence[str] = dataclasses.field(default_factory=list)


class Command(abc.ABC):
    def __init__(self, initialiser: CommandLike) -> None:
        self.callback = initialiser.callback
        self.name = initialiser.name
        self.description = initialiser.description
        self.options = initialiser.options
        self.checks = initialiser.checks
        self.cooldown_manager = initialiser.cooldown_manager
        self.error_handler = initialiser.error_handler

    async def __call__(self, context: context_.base.Context) -> None:
        return await self.callback(context)

    @abc.abstractmethod
    def signature(self) -> str:
        ...

    async def invoke(self, context: context_.base.Context) -> None:
        await self.evaluate_checks(context)
        await self.evaluate_cooldowns(context)
        await self(context)

    async def evaluate_checks(self, context: context_.base.Context) -> bool:
        failed_checks: t.List[errors.CheckFailure] = []
        for check in self.checks:
            try:
                result = check(context)
                if inspect.iscoroutine(result):
                    assert not isinstance(result, bool)
                    result = await result

                if not result:
                    failed_checks.append(errors.CheckFailure(f"Check {check.__name__} failed for command {self.name}"))
            except Exception as ex:
                error = errors.CheckFailure(str(ex))
                error.__cause__ = ex
                failed_checks.append(error)

        if len(failed_checks) > 1:
            raise errors.CheckFailure("Multiple checks failed: " + ", ".join(str(ex) for ex in failed_checks))
        elif failed_checks:
            raise failed_checks[0]

        return True

    async def evaluate_cooldowns(self, context: context_.base.Context) -> None:
        if self.cooldown_manager is not None:
            pass
