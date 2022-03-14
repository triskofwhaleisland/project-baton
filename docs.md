# Project BATON
Version: T is for Transitional
Programming specifics: Uses Python 3.10, requires libraries `py-cord` (a d.py fork) and `PyYAML` (to store recruitment data).
# Structures
## RecruitmentStatus
`READY` (to recruit) or `ACTIVE`(ly recruiting). 
(Inherits from stdlib `enum.Enum`.)
## RecruitQueue
Basically a fancy `dict`. Made up of `discord.Member: RecruitmentStatus` pairs. Has a special property, `active_user` (type `discord.Member | None`) to refer to the user that is currently `ACTIVE`(ly recruiting.)
(Uses stdlib `dataclasses.dataclass` wrapper.)
# Commands
## set_status \[status]
Changes the status of the user to a `RecruitmentStatus`. Cannot change status to `ACTIVE` if another user is already `ACTIVE`.
### aliases
**join** = set_status active
**ready** = set_status ready
## leave
Removes a user from the queue completely.
## display
Provides an embed listing the users in the queue (including the `ACTIVE` user).
## ping \[status] \<message>
Pings all member(s) of a `RecruitmentStatus` with an optional message. Output is in the form of `author -> targets: message`.