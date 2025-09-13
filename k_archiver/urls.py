from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import RedirectView
from . import settings

admin.site.site_header = 'K-Achiver Admin'
admin.site.site_title = 'K-Achiver Admin'
admin.site.index_title = 'For admins only'

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
import subprocess
import os


import subprocess

def get_gpg_token(gpg_file: str = "~/.githubhook_k_archiver.gpg", passphrase_file: str = "/tmp/gpg-passphrase") -> str:
    try:
        gpg_file = os.path.expanduser(gpg_file)
        cmd = [
            "gpg",
            "--batch",
            "--quiet",
            "--yes",
            "--passphrase-file", passphrase_file,
            "--decrypt",
            gpg_file
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to decrypt token: {e.stderr.strip()}"
        raise RuntimeError(error_msg) from e


@csrf_exempt
def github_webhook(request):
    if request.method != 'POST':
        return HttpResponse('Ntaco mukora aha', status=405)

    
    event = request.headers.get('X-GitHub-Event', '')
    if event != 'push':
        return HttpResponse('Iyo si push man !', status=200)
    
    # Path to your project directory server
    project_dir = '/home/ksquadde/api.k-archiver.ksquad.dev/k-archiver-backend'
    passenger_dir = '/home/ksquadde/api.k-archiver.ksquad.dev'

    # Path to your virtual environment's Python and pip executables
    venv_dir = '/home/ksquadde/virtualenv/api.k-archiver.ksquad.dev/3.11'
    # Adjust the path to your virtual environment's Python and pip executables
    venv_python = os.path.join(venv_dir, 'bin/python')
    venv_pip = os.path.join(venv_dir, 'bin/pip')

    token = get_gpg_token()
    repo_url = f"https://{token}@github.com/K-SQUAD/k-archiver-backend.git"
    
    try:
         # Pull the latest changes
        subprocess.run(['git', '-C', project_dir, 'pull',repo_url], check=True)
        subprocess.run([venv_python, os.path.join(project_dir, 'manage.py'), 'makemigrations'], check=True)
        subprocess.run([venv_python, os.path.join(project_dir, 'manage.py'), 'migrate'], check=True)
        
        subprocess.run(['touch', os.path.join(passenger_dir, 'passenger_wsgi.py')], check=True)
        return HttpResponse('Deployment successful', status=200)
    except subprocess.CalledProcessError as e:
        return HttpResponse(f'Deployment failed: {str(e)}', status=500)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/',include('api.urls')),
    path('githubhook/', github_webhook, name='github_webhook'),
    path('',RedirectView.as_view(url='/api/')),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)