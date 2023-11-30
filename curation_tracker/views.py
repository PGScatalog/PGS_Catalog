import datetime as dt
from django.shortcuts import render
from django.conf import settings
from django.db.models import Count
from .tables import *

curation_tracker = 'curation_tracker'
l1_curation_done = ['Curation done','Curation done (AS)']
not_awaiting_curation = [*l1_curation_done,'Determined ineligible']

# Create your views here.

def browse_l1_waiting(request):
    l1_waiting = CurationPublicationAnnotation.objects.using(curation_tracker).exclude(first_level_date__isnull=True,second_level_date__isnull=True).exclude(first_level_curation_status__in=not_awaiting_curation)
    table_l1 = Browse_CurationPublicationAnnotationL1(l1_waiting)
    context = {
        'table': table_l1,
        'has_table': 1
    }
    return render(request, 'curation_tracker/l1_curation.html', context)

def browse_l2_waiting(request):
    l2_waiting = CurationPublicationAnnotation.objects.using(curation_tracker).filter(first_level_date__isnull=False,first_level_curation_status__in=l1_curation_done).exclude(second_level_curation_status__in=not_awaiting_curation)
    table_l2 = Browse_CurationPublicationAnnotationL2(l2_waiting)
    context = {
      'table': table_l2,
      'has_table': 1
    }
    return render(request, 'curation_tracker/l2_curation.html', context)


def browse_release_ready(request):
    context = {}
    import_ready_count = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Curated - Awaiting Import').count()
    context['studies_to_import_count'] = import_ready_count
    if import_ready_count:
        import_ready = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Curated - Awaiting Import')
        context['table_to_import'] = Browse_CurationPublicationAnnotationReleaseReady(import_ready)

    release_ready_count = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Imported - Awaiting Release').count()
    context['studies_to_release_count'] = release_ready_count
    if release_ready_count:
        release_ready = CurationPublicationAnnotation.objects.using(curation_tracker).filter(curation_status='Imported - Awaiting Release')
        context['table_to_release'] = Browse_CurationPublicationAnnotationReleaseReady(release_ready)

    if context:
        context['has_table'] = 1
    return render(request, 'curation_tracker/release_ready.html', context)


def validate_metadata_template(request):
    context = {}
    from django.core.files.storage import default_storage
    if request.method == 'POST' and request.FILES['myfile']:
        if settings.MIN_UPLOAD_SIZE <= request.FILES['myfile'].size <= settings.MAX_UPLOAD_SIZE:
            file_name = request.FILES['myfile'].name
            file_content = request.FILES['myfile'].read()
            file = default_storage.open(file_name, 'w')
            file.write(file_content)
            file.close()
            context['uploaded_file'] = True
            context['filename'] = file_name
        else:
            error_msg = 'There is an issue regarding the uploaded file size'
            # File too big
            if request.FILES['myfile'].size > settings.MAX_UPLOAD_SIZE:
                error_msg = 'The uploaded file size is too big (>'+settings.MAX_UPLOAD_SIZE_LABEL+')'
            # File too small
            elif request.FILES['myfile'].size < settings.MIN_UPLOAD_SIZE:
                error_msg = 'The uploaded file size looks too small ('+str(request.FILES['myfile'].size)+'b)'
            context['size_error'] = error_msg
    context['max_upload_size_label'] = settings.MAX_UPLOAD_SIZE_LABEL
    return render(request, 'curation_tracker/validate_metadata.html', context)


def stats(request):
    context = {}

    ## L1 curation
    context['l1_curation'] = []

    # L1 - Author submission
    l1_as_queryset = (CurationPublicationAnnotation.objects.using(curation_tracker)
        .filter(first_level_curation_status__in=['Author submission','Curation done (AS)'])
        .values('first_level_date__month','first_level_date__year') # Group By year and month
        .annotate(c=Count('id'))                                    # Select the count of the grouping
        .order_by('-first_level_date__year', '-first_level_date__month')
    )
    l1_as_data = {}
    for l1_as in l1_as_queryset:
        if l1_as['first_level_date__month']:
            month_num = str(l1_as['first_level_date__month'])
            datetime_object = dt.datetime.strptime(month_num, "%m")
            month_name = datetime_object.strftime("%B")
            year = l1_as['first_level_date__year']
            count = l1_as['c']
            if year not in l1_as_data.keys():
                l1_as_data[year] = {}
            l1_as_data[year][month_name] = count

    # L1 curation done
    l1_queryset = (CurationPublicationAnnotation.objects.using(curation_tracker)
        .filter(first_level_curation_status__in=['Curation done','Curation done (AS)','Author submission'])
        .values('first_level_date__month','first_level_date__year') # Group By year and month
        .annotate(c=Count('id'))                                    # Select the count of the grouping
        .order_by('-first_level_date__year', '-first_level_date__month')
    )
    for l1 in l1_queryset:
        if l1['first_level_date__month']:
            month_num = l1['first_level_date__month']
            datetime_object = dt.datetime.strptime(str(month_num), "%m")
            month_name = datetime_object.strftime("%B")
            year = l1['first_level_date__year']
            studies = (CurationPublicationAnnotation.objects.using(curation_tracker)
                .filter(first_level_date__month=month_num, first_level_date__year=year)
                .values('num','id','study_name')
                .order_by('id')
            )
            studies_list_html = studies2html(f'l1_{year}_{month_num}',studies)
            l1_data = {
                'month': month_name,
                'year': l1['first_level_date__year'],
                'count': l1['c'],
                'studies': studies_list_html
            }
            l1_as_count = 0
            if year in l1_as_data.keys():
                if month_name in l1_as_data[year].keys():
                    l1_as_count = l1_as_data[year][month_name]
            l1_data['author_submission'] = l1_as_count
            context['l1_curation'].append(l1_data)

    ## L2 Curation ##
    # L2 curation done
    context['l2_curation'] = []
    l2_queryset = (CurationPublicationAnnotation.objects.using(curation_tracker)
        .filter(second_level_curation_status__in=['Curation done'])
        .values('second_level_date__month','second_level_date__year') # Group By year and month
        .annotate(c=Count('id'))                                      # Select the count of the grouping
        .order_by('-second_level_date__year', '-second_level_date__month')
    )
    for l2 in l2_queryset:
        if l2['second_level_date__month']:
            month_num = l2['second_level_date__month']
            datetime_object = dt.datetime.strptime(str(month_num), "%m")
            month_name = datetime_object.strftime("%B")
            year = l2['second_level_date__year']
            studies = (CurationPublicationAnnotation.objects.using(curation_tracker)
                .filter(second_level_date__month=month_num, second_level_date__year=year)
                .values('num','id','study_name')
                .order_by('id')
            )
            studies_list_html = studies2html(f'l2_{year}_{month_num}',studies)
            l2_data = {
                'month': month_name,
                'year': l2['second_level_date__year'],
                'count': l2['c'],
                'studies': studies_list_html
            }
            context['l2_curation'].append(l2_data)

    return render(request, 'curation_tracker/curation_stats.html', context)


def studies2html(row_id,studies):
    html = f'<a class="toggle_btn pgs_btn_plus pgs_no_icon_link ml-1" id="{row_id}" data-toggle="tooltip" title="Click to display the list of Studies"></a>'
    html = html + f'<div class="toggle_list mt-2" id="list_{row_id}">\n<ul>'
    for study in studies:
        html = html + f'<li><a href="/admin/curation_tracker/curationpublicationannotation/{study["num"]}/change/">{study["id"]}</a> ({study["study_name"]})</li>'
    html = html + '</ul>\n</div>'
    return html
