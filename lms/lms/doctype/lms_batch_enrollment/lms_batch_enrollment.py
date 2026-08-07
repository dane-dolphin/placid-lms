# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.email.doctype.email_template.email_template import get_email_template
from frappe.model.document import Document


class LMSBatchEnrollment(Document):
	def after_insert(self):
		send_confirmation_email(self)
		self.add_member_to_live_class()
		enroll_member_in_batch_courses(self.batch, self.member)

	def validate(self):
		self.validate_duplicate_members()

	def validate_duplicate_members(self):
		if frappe.db.exists(
			"LMS Batch Enrollment",
			{"batch": self.batch, "member": self.member, "name": ["!=", self.name]},
		):
			frappe.throw(_("Member already enrolled in this batch"))

	def add_member_to_live_class(self):
		live_classes = frappe.get_all("LMS Live Class", {"batch_name": self.batch}, ["name", "event"])

		for live_class in live_classes:
			if live_class.event:
				frappe.get_doc(
					{
						"doctype": "Event Participants",
						"reference_doctype": "User",
						"reference_docname": self.member,
						"email": self.member,
						"parent": live_class.event,
						"parenttype": "Event",
						"parentfield": "event_participants",
					}
				).save()


def enroll_member_in_batch_courses(batch, member):
	"""Enrol one member into every course attached to a batch.

	Returns the list of courses the member was newly enrolled into.
	"""
	return enroll_members_in_batch_courses(batch, [member]).get(member, [])


def enroll_members_in_batch_courses(batch, members):
	"""Enrol several members into every course attached to a batch.

	Deliberately runs outside `validate` so the batch enrollment row is committed
	before the course enrollments are created, and with `ignore_permissions` because
	a Batch Evaluator has no create right on LMS Enrollment but is expected to be
	able to add students to their own batch. Idempotent - safe to re-run.

	Existing enrollments are resolved in a single query rather than one per
	(member, course) pair, so saving a large batch stays cheap.

	Returns {member: [courses newly enrolled into]}.
	"""
	members = [m for m in dict.fromkeys(members) if m]
	enrolled = {member: [] for member in members}
	if not members:
		return enrolled

	courses = frappe.get_all(
		"Batch Course",
		filters={"parent": batch, "parenttype": "LMS Batch"},
		pluck="course",
	)
	courses = [c for c in dict.fromkeys(courses) if c]
	if not courses:
		return enrolled

	existing = {
		(row.course, row.member)
		for row in frappe.get_all(
			"LMS Enrollment",
			filters={"course": ["in", courses], "member": ["in", members]},
			fields=["course", "member"],
		)
	}

	for member in members:
		for course in courses:
			if (course, member) in existing:
				continue

			try:
				enrollment = frappe.new_doc("LMS Enrollment")
				enrollment.course = course
				enrollment.member = member
				enrollment.insert(ignore_permissions=True)
				enrolled[member].append(course)
			except Exception:
				# One bad pair must not block the rest of the batch, but it must not
				# fail silently either - the previous version swallowed this entirely.
				frappe.log_error(
					title="Batch course enrollment failed",
					message=f"batch={batch} member={member} course={course}\n\n{frappe.get_traceback()}",
				)

	return enrolled


@frappe.whitelist()
def send_confirmation_email(doc):
	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	if not doc.confirmation_email_sent:
		outgoing_email_account = frappe.get_cached_value(
			"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
		)
		if not doc.confirmation_email_sent and (outgoing_email_account or frappe.conf.get("mail_login")):
			send_mail(doc)
			frappe.db.set_value(doc.doctype, doc.name, "confirmation_email_sent", 1)


def send_mail(doc):
	batch = frappe.db.get_value(
		"LMS Batch",
		doc.batch,
		[
			"name",
			"title",
			"start_date",
			"start_time",
			"medium",
			"confirmation_email_template",
		],
		as_dict=1,
	)

	subject = _("Enrollment Confirmation for {0}").format(batch.title)
	template = "batch_confirmation"
	custom_template = batch.confirmation_email_template or frappe.db.get_single_value(
		"LMS Settings", "batch_confirmation_template"
	)

	args = {
		"title": batch.title,
		"student_name": doc.member_name,
		"start_time": batch.start_time,
		"start_date": batch.start_date,
		"medium": batch.medium,
		"name": batch.name,
	}

	if custom_template:
		email_template = get_email_template(custom_template, args)
		subject = email_template.get("subject")
		content = email_template.get("message")

	frappe.sendmail(
		recipients=doc.member,
		subject=subject,
		template=template if not custom_template else None,
		content=content if custom_template else None,
		args=args,
		header=[_(batch.title), "green"],
		retry=3,
	)
