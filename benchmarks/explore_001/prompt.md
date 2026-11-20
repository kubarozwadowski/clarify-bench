# Add a project lookup handler

Implement `get_project(projects, project_id)` in `project/handlers.py`. Use the
same response and error conventions as the existing lookup handlers. A successful
lookup returns the stored project. A missing project should follow the established
missing-resource convention, using resource name `project`. Preserve the existing
handlers. These are plain Python functions; no web server is needed.
