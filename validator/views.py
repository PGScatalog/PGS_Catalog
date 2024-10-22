from django.shortcuts import render


def validate_metadata_template_client(request):
    return render(request, 'validator/validate_metadata_client.html', {})


def validate_scoring_files_client(request):
    return render(request, 'validator/validate_scoring_files_client.html', {})
