from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ProjectFile
from .forms import FileUploadForm
from apps.projects.models import Project
import os

@login_required
def file_list(request):
    """List all files user has access to"""
    if request.user.role == 'SUPER_ADMIN':
        files = ProjectFile.objects.all()
    else:
        # Get files from projects user is part of
        projects = Project.objects.filter(
            Q(project_manager=request.user) | Q(team_members=request.user)
        )
        files = ProjectFile.objects.filter(project__in=projects)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        files = files.filter(Q(filename__icontains=search_query) | Q(description__icontains=search_query))
    
    # Filter by file type
    file_type = request.GET.get('type', '')
    if file_type:
        files = files.filter(file_type=file_type)
    
    # Pagination
    paginator = Paginator(files, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'files': page_obj,
        'search_query': search_query,
        'file_type': file_type,
    }
    return render(request, 'files/file_list.html', context)

@login_required
def file_upload(request):
    """Upload file to project"""
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            # Create file record
            project_file = ProjectFile(
                file=uploaded_file,
                filename=uploaded_file.name,
                file_size=uploaded_file.size,
                project=form.cleaned_data['project'],
                uploaded_by=request.user,
                description=form.cleaned_data['description']
            )
            
            # Determine file type
            extension = uploaded_file.name.split('.')[-1].lower()
            if extension in ['pdf']:
                project_file.file_type = 'PDF'
            elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                project_file.file_type = 'IMAGE'
            elif extension in ['doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx']:
                project_file.file_type = 'DOCUMENT'
            elif extension in ['zip', 'rar', '7z', 'tar', 'gz']:
                project_file.file_type = 'ARCHIVE'
            else:
                project_file.file_type = 'OTHER'
            
            project_file.save()
            
            messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
            return redirect('file_list')
    else:
        form = FileUploadForm(user=request.user)
    
    return render(request, 'files/file_upload.html', {'form': form})

@login_required
def file_download(request, pk):
    """Download file"""
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    
    # Check permission
    if request.user.role != 'SUPER_ADMIN' and \
       request.user != file_obj.project.project_manager and \
       request.user not in file_obj.project.team_members.all():
        messages.error(request, 'You do not have permission to download this file.')
        return redirect('file_list')
    
    # Increment download count
    file_obj.download_count += 1
    file_obj.save()
    
    # Serve file
    file_path = file_obj.file.path
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = f'attachment; filename="{file_obj.filename}"'
            return response
    else:
        raise Http404("File not found")

@login_required
def file_delete(request, pk):
    """Delete file"""
    file_obj = get_object_or_404(ProjectFile, pk=pk)
    
    # Check permission
    if request.user.role != 'SUPER_ADMIN' and request.user != file_obj.uploaded_by:
        messages.error(request, 'You do not have permission to delete this file.')
        return redirect('file_list')
    
    if request.method == 'POST':
        filename = file_obj.filename
        
        # Delete physical file
        if os.path.isfile(file_obj.file.path):
            os.remove(file_obj.file.path)
        
        file_obj.delete()
        messages.success(request, f'File "{filename}" deleted successfully!')
        return redirect('file_list')
    
    return render(request, 'files/file_confirm_delete.html', {'file': file_obj})