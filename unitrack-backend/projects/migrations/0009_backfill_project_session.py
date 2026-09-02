from django.db import migrations


def backfill_project_sessions(apps, schema_editor):
    """Deterministically assign each project a session.

    Preference: the session whose date range covers the project's
    ``created_at``; otherwise the most recently started session. Projects with
    no existing sessions available are left unassigned (the field is nullable).
    """
    Project = apps.get_model('projects', 'Project')
    ProjectSession = apps.get_model('projects', 'ProjectSession')

    sessions = list(ProjectSession.objects.all().order_by('start_date', 'id'))
    if not sessions:
        return
    latest = max(sessions, key=lambda s: (s.start_date, s.id))

    for project in Project.objects.filter(session__isnull=True).select_related('session'):
        created = project.created_at.date() if project.created_at else None
        match = None
        if created is not None:
            for session in sessions:
                if session.start_date <= created <= session.end_date:
                    match = session
                    break
        if match is None:
            match = latest
        project.session = match
        project.save(update_fields=['session'])


def unset_project_sessions(apps, schema_editor):
    Project = apps.get_model('projects', 'Project')
    Project.objects.update(session=None)


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_project_session_project_tags_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_project_sessions, unset_project_sessions),
    ]
