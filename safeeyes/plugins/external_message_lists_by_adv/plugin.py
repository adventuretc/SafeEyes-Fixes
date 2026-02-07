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

Reads message files from configured paths and injects the messages into
the break queues (short_breaks / long_breaks) in the config.

File format:
	Messages are separated by a single - (dash) at the start of a line.
	The remainder of that line (after the dash and optional whitespace) is
	the beginning of the next message. A message can span multiple lines.
	Messages are trimmed for leading/trailing whitespace.

	Escape code:
		\\- at the start of a line produces a literal - at the start of
		that line inside the message (the backslash is consumed).

	Mid-line and end-of-line dashes are always literal.

Config example (in safeeyes.json plugins array):
	{
		"enabled": true,
		"id": "external_message_lists_by_adv",
		"settings": {
			"message_file_paths": [
				{
					"path": "~/some file.d",
					"appears_in": ["short_breaks", "long_breaks"]
				},
				{
					"path": "~/another file.d",
					"appears_in": ["short_breaks"]
				},
				"~/plain path defaults to both.d"
			]
		},
		"version": "1.0.0"
	}

	Each entry can be:
	- A plain string path (defaults to appearing in both short_breaks and long_breaks)
	- A dict with "path" and optional "appears_in" (list of "short_breaks" / "long_breaks")
"""

import logging
import os
import re


def _parse_message_file(content):
	"""Parse a message file using the - at start of line separator format.

	Rules:
	- A line starting with a single - (dash) starts a new message.
	  The remainder of that line (after the dash and optional space) is the
	  beginning of the new message.
	- A line starting with \\- is an escaped dash: it produces a literal -
	  at the start of that line within the current message.
	- Mid-line and end-of-line dashes are always literal / part of the message.
	- Messages are trimmed for whitespace on their start and end.
	"""
	messages = []
	current_message_lines = []

	for line in content.split("\n"):
		# re.search("^...$") is used because re.match() is shit:
		# it returns true even if only the beginning of the string matches.
		if re.search(r"^-\s?", line):
			# This line starts a new message.
			# First, save the previous message if any.
			if current_message_lines:
				msg = "\n".join(current_message_lines).strip()
				if msg:
					messages.append(msg)
			# Start the new message with the remainder after the dash
			remainder = re.sub(r"^-\s?", "", line)
			current_message_lines = [remainder]
		elif re.search(r"^\\-", line):
			# Escaped dash: produce a literal - at the start of the line
			# (consume the backslash)
			unescaped_line = line[1:]  # remove the leading backslash
			current_message_lines.append(unescaped_line)
		else:
			# Continuation of the current message (or content before first -)
			current_message_lines.append(line)

	# Don't forget the last message
	if current_message_lines:
		msg = "\n".join(current_message_lines).strip()
		if msg:
			messages.append(msg)

	return messages


def _parse_path_entries(raw_entries):
	"""Parse path entries from the config.

	Each entry can be:
	- A plain string path (defaults to ["short_breaks", "long_breaks"])
	- A dict with "path" and optional "appears_in"

	Returns a list of (resolved_path, appears_in_set) tuples.
	"""
	result = []
	default_appears_in = {"short_breaks", "long_breaks"}

	if not isinstance(raw_entries, list):
		logging.warning(
			"External Message Lists plugin: message_file_paths should be a list, got %s",
			type(raw_entries),
		)
		return result

	for entry in raw_entries:
		if isinstance(entry, str):
			path = entry.strip()
			appears_in = default_appears_in
		elif isinstance(entry, dict):
			path = entry.get("path", "")
			if isinstance(path, str):
				path = path.strip()
			else:
				logging.warning(
					"External Message Lists plugin: 'path' in entry should be a string, got %s",
					type(path),
				)
				continue
			raw_appears = entry.get("appears_in", None)
			if raw_appears is None:
				appears_in = default_appears_in
			elif isinstance(raw_appears, list):
				appears_in = set()
				for item in raw_appears:
					if item in ("short_breaks", "long_breaks"):
						appears_in.add(item)
					else:
						logging.warning(
							"External Message Lists plugin: unknown appears_in value: %s (expected 'short_breaks' or 'long_breaks')",
							item,
						)
				if not appears_in:
					appears_in = default_appears_in
			else:
				logging.warning(
					"External Message Lists plugin: 'appears_in' should be a list, got %s",
					type(raw_appears),
				)
				appears_in = default_appears_in
		else:
			logging.warning(
				"External Message Lists plugin: unexpected entry type in message_file_paths: %s",
				type(entry),
			)
			continue

		if not path:
			continue

		# Resolve ~ to the current user's home directory
		resolved_path = os.path.expanduser(path)
		result.append((resolved_path, appears_in))

	return result


def init(ctx, safeeyes_config, plugin_config):
	"""Initialize the plugin.

	Reads all message files and injects the parsed messages into the
	safeeyes_config's short_breaks and/or long_breaks lists.
	This way, when the core rebuilds its break queue after plugins init,
	the external messages are already part of the break config and appear
	as normal breaks.
	"""
	raw_entries = plugin_config.get("message_file_paths", [])
	path_entries = _parse_path_entries(raw_entries)

	if not path_entries:
		logging.info("External Message Lists plugin: no message file paths configured")
		return

	# Collect messages per target queue
	messages_for_short = []
	messages_for_long = []

	for resolved_path, appears_in in path_entries:
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

		messages = _parse_message_file(content)

		if not messages:
			logging.warning("External Message Lists plugin: no messages found in %s", resolved_path)
			continue

		logging.info(
			"External Message Lists plugin: loaded %d messages from %s (appears_in: %s)",
			len(messages),
			resolved_path,
			appears_in,
		)

		if "short_breaks" in appears_in:
			messages_for_short.extend(messages)
		if "long_breaks" in appears_in:
			messages_for_long.extend(messages)

	# Inject messages into the config's break lists as break config dicts.
	# These have the same format as the built-in break entries: {"name": "..."}
	# The BreakQueue.__build_queue() will pick them up when it builds the queue.
	total_injected = 0

	if messages_for_short:
		short_breaks = safeeyes_config.get("short_breaks")
		if short_breaks is not None and isinstance(short_breaks, list):
			for msg in messages_for_short:
				short_breaks.append({"name": msg})
				total_injected += 1

	if messages_for_long:
		long_breaks = safeeyes_config.get("long_breaks")
		if long_breaks is not None and isinstance(long_breaks, list):
			for msg in messages_for_long:
				long_breaks.append({"name": msg})
				total_injected += 1

	logging.info(
		"External Message Lists plugin: injected %d break entries total (%d short, %d long)",
		total_injected,
		len(messages_for_short),
		len(messages_for_long),
	)