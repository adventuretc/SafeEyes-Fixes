# Safe Eyes is a utility to remind you to take break frequently
# to protect your eyes from eye strain.

# Copyright (C) 2026  adventuretc

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
External Message Lists plugin for Safe Eyes.

Reads message files from configured paths. Each file contains messages
separated by @@ (two at signs). Messages are trimmed for whitespace.
These messages replace the break name with a random message from the pool
before each break is shown.
"""

import logging
import os
import random

# The pool of messages loaded from external files
_messages = []


def init(ctx, safeeyes_config, plugin_config):
	"""Initialize the plugin.

	Reads all message files specified in the plugin config and builds
	the message pool. Paths may use ~ for the home directory.

	The paths can be configured as:
	- An array of strings in the JSON config (e.g. ["~/path1.d", "~/path2.d"])
	- A single newline-separated string (from the settings UI text field)
	"""
	global _messages
	_messages = []

	# The config can store paths as either an array or a newline-separated string
	raw_paths = plugin_config.get("message_file_paths", "")
	if isinstance(raw_paths, list):
		# Array format from JSON config
		paths = [p.strip() for p in raw_paths if isinstance(p, str) and p.strip()]
	elif isinstance(raw_paths, str):
		# Newline-separated string from settings UI
		if not raw_paths.strip():
			logging.warning("External Message Lists plugin: no message file paths configured")
			return
		paths = [line.strip() for line in raw_paths.strip().split("\n") if line.strip()]
	else:
		logging.warning("External Message Lists plugin: unexpected type for message_file_paths: %s", type(raw_paths))
		return

	if not paths:
		logging.warning("External Message Lists plugin: no message file paths configured")
		return

	for path in paths:
		# Resolve ~ to the current user's home directory
		resolved_path = os.path.expanduser(path)

		if not os.path.isfile(resolved_path):
			logging.warning("External Message Lists plugin: file not found: %s", resolved_path)
			continue

		try:
			with open(resolved_path, "r", encoding="utf-8") as f:
				content = f.read()
		except PermissionError:
			logging.error(
				"External Message Lists plugin: permission denied reading file: %s",
				resolved_path,
			)
			continue
		except Exception as e:
			logging.error(
				"External Message Lists plugin: error reading file %s: %s",
				resolved_path,
				e,
			)
			continue

		# Split messages by @@ separator and trim whitespace
		raw_messages = content.split("@@")
		for msg in raw_messages:
			trimmed = msg.strip()
			if trimmed:
				_messages.append(trimmed)

	logging.info(
		"External Message Lists plugin: loaded %d messages from %d file(s)",
		len(_messages),
		len(paths),
	)


# def on_pre_break(break_obj):
# 	"""Replace the break name with a random message from the external pool.

# 	Called before each break is shown. If the message pool is non-empty,
# 	the break's name is replaced with a randomly chosen message.
# 	"""
# 	break_obj.name = "debug1"
# 	if _messages:
# 		break_obj.name = random.choice(_messages)

# def on_start_break(break_obj):
# 	break_obj.name = "debug2"
# 	if _messages:
# 		break_obj.name = random.choice(_messages)