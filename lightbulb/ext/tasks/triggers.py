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

__all__ = ["Trigger", "UniformTrigger", "CronTrigger"]

import abc
import datetime


class Trigger(abc.ABC):
    """
    Base class representing a task trigger.
    """

    __slots__ = ()

    @abc.abstractmethod
    def get_interval(self) -> float:
        """
        Get the interval to sleep for in seconds until the next run of the task.

        Returns:
            :obj:`float`: Seconds to sleep until the next time the task is run.
        """
        ...


class UniformTrigger(Trigger):
    """
    A uniform interval task trigger. Tasks will always be run with the same interval between them.

    Args:
        interval (:obj:`float`): Number of seconds between task executions.
    """

    __slots__ = ("_interval",)

    def __init__(self, interval: float) -> None:
        self._interval = interval

    def get_interval(self) -> float:
        return self._interval


try:
    import croniter

    class CronTrigger(Trigger):
        """
        A crontab-based task trigger. Tasks will be run dependent on the given crontab.

        Args:
            crontab (:obj:`str`): Schedule that task executions will follow.

        Note:
            This trigger is only available when installing lightbulb with the ``[crontrigger]`` option.

            See: ``pip install hikari-lightbulb[crontrigger]``
        """

        __slots__ = ("_croniter",)

        def __init__(self, crontab: str) -> None:
            self._croniter = croniter.croniter(crontab, datetime.datetime.now(datetime.timezone.utc))

        def get_interval(self) -> float:
            difference: datetime.timedelta = self._croniter.get_next(datetime.datetime) - datetime.datetime.now(
                datetime.timezone.utc
            )
            return difference.total_seconds()

except ModuleNotFoundError:

    class CronTrigger(Trigger):  # type: ignore[no-redef]
        __slots__ = ()

        def __init__(self, _: str) -> None:
            raise ModuleNotFoundError(
                "'CronTrigger' is not available. Install lightbulb with option '[crontrigger]' to enable"
            )

        def get_interval(self) -> float:
            raise NotImplementedError
