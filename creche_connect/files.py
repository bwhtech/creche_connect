import frappe
from frappe import _

MAX_AUDIO_MB = 10


def check_audio_size(doc, method=None):
	if (getattr(doc, "content_type", None) or "").startswith("audio/") and (doc.file_size or 0) > MAX_AUDIO_MB * 1024 * 1024:
		frappe.throw(_("Audio can be up to {0} MB").format(MAX_AUDIO_MB))
