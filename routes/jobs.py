from flask import render_template, request, redirect, url_for, flash, abort, Response
from flask_login import login_required, current_user
from extensions import db
from models import Job
from routes import jobs_bp
from datetime import date
from sqlalchemy import extract
import csv
from io import StringIO

@jobs_bp.get("/dashboard")
@login_required
def dashboard():
    # --- read filters from query string ---
    status = (request.args.get("status") or "").strip()        # "", "Applied", "Interview", "Offer", "Rejected"
    q = (request.args.get("q") or "").strip()                  # search term for company/role
    month = (request.args.get("month") or "").strip()          # "YYYY-MM" from <input type="month">

    # --- base query (only current user's jobs) ---
    base = Job.query.filter_by(user_id=current_user.id)

    # --- apply filters ---
    filtered = base

    if status:
        filtered = filtered.filter(Job.status == status)

    if q:
        like = f"%{q}%"
        filtered = filtered.filter(
            db.or_(Job.company.ilike(like), Job.role.ilike(like))
        )

    if month:
        try:
            y, m = map(int, month.split("-"))
            filtered = filtered.filter(
                Job.applied_on.isnot(None),
                extract("year", Job.applied_on) == y,
                extract("month", Job.applied_on) == m,
            )
        except Exception:
            pass


    jobs = filtered.order_by(Job.created_at.desc()).all()
    # --- counts for sidebar ---
    counts = {
        "Applied":   base.filter(Job.status == "Applied").count(),
        "Interview": base.filter(Job.status == "Interview").count(),
        "Offer":     base.filter(Job.status == "Offer").count(),
        "Rejected":  base.filter(Job.status == "Rejected").count(),
        "Total":     base.count(),
    }

    return render_template(
        "dashboard.html",
        jobs=jobs,
        user=current_user,
        counts=counts,
        status=status,
        q=q,
        month=month,
    )

@jobs_bp.get("/new")
@login_required
def new_job_form():
    return render_template("job_new.html")

@jobs_bp.post("/new")
@login_required
def new_job_submit():
    company = (request.form.get("company") or "").strip()
    role = (request.form.get("role") or "").strip()
    status = (request.form.get("status") or "Applied").strip()
    location = (request.form.get("location") or "").strip()
    link = (request.form.get("link") or "").strip()
    applied_on = (request.form.get("applied_on") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not company or not role:
        flash("Company and Role are required.", "error")
        return redirect(url_for("jobs.new_job_form"))

    parsed_date = None
    if applied_on:
        try:
            y, m, d = map(int, applied_on.split("-"))
            parsed_date = date(y, m, d)
        except Exception:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            return redirect(url_for("jobs.new_job_form"))

    job = Job(user_id=current_user.id, company=company, role=role, status=status,
              location=location, link=link, applied_on=parsed_date, notes=notes)
    db.session.add(job)
    db.session.commit()
    flash("Job saved.", "success")
    return redirect(url_for("jobs.dashboard"))

def _get_job_or_404(job_id):
    job = Job.query.get_or_404(job_id)
    if job.user_id != current_user.id:
        abort(403)
    return job

@jobs_bp.get("/<int:job_id>/edit")
@login_required
def edit_form(job_id):
    job = _get_job_or_404(job_id)
    return render_template("job_edit.html", job=job)

@jobs_bp.post("/<int:job_id>/edit")
@login_required
def edit_submit(job_id):
    job = _get_job_or_404(job_id)

    company = (request.form.get("company") or "").strip()
    role = (request.form.get("role") or "").strip()
    status = (request.form.get("status") or "Applied").strip()
    location = (request.form.get("location") or "").strip()
    link = (request.form.get("link") or "").strip()
    applied_on = (request.form.get("applied_on") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not company or not role:
        flash("Company and Role are required.", "error")
        return redirect(url_for("jobs.edit_form", job_id=job.id))

    parsed_date = None
    if applied_on:
        try:
            y, m, d = map(int, applied_on.split("-"))
            parsed_date = date(y, m, d)
        except Exception:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            return redirect(url_for("jobs.edit_form", job_id=job.id))

    job.company = company
    job.role = role
    job.status = status
    job.location = location
    job.link = link
    job.applied_on = parsed_date
    job.notes = notes

    db.session.commit()
    flash("Job updated.", "success")
    return redirect(url_for("jobs.dashboard"))

@jobs_bp.post("/<int:job_id>/delete")
@login_required
def delete(job_id):
    job = _get_job_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "success")
    return redirect(url_for("jobs.dashboard"))

@jobs_bp.get("/export.csv")
@login_required
def export_csv():
    # get all current user's jobs
    jobs = Job.query.filter_by(user_id=current_user.id).order_by(Job.created_at).all()

    # prepare CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    # header row
    writer.writerow(["Company", "Role", "Status", "Location", "Applied On", "Link", "Notes"])

    # data rows
    for j in jobs:
        writer.writerow([
            j.company,
            j.role,
            j.status,
            j.location or "",
            j.applied_on or "",
            j.link or "",
            (j.notes or "").replace("\n", " "),  # keep single-line
        ])

    # return as downloadable file
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=jobs.csv"}
    )