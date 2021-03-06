from django.conf import settings
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from socialauth.lib.linkedin import LinkedIn
from web.helpers import extract_skills_from_user_string, get_skills_info, \
  update_skills_for_member
from web.models import Project, Member
from socialauth.models import LinkedInUserProfile

def index(request):
  logged_in = request.user.is_authenticated()
  if logged_in == False:
    return render_to_response('index.html', {'logged_in' : logged_in,})
  else:
    return redirect('web.views.dashboard')

def dashboard(request):
  ln_user_id = str(request.user)[3:]
  ln_user = LinkedInUserProfile.objects.get(linkedin_uid = ln_user_id)
  projects = Project.objects.filter(creator = ln_user)
  for project in projects:
    project.skills_info = get_skills_info(project)

  d = {'projects': projects}
  return render_to_response('dashboard.html', d, RequestContext(request))

def project(request, id):
  project = Project.objects.get(pk=id)
  return render_to_response('project/project.html', { 'project': project}, RequestContext(request))

def project_create(request):
  if request.method == 'POST':
    ln_user_id = str(request.user)[3:]
    ln_user = LinkedInUserProfile.objects.get(linkedin_uid = ln_user_id)
    name = request.POST['name']
    skills = extract_skills_from_user_string(request.POST['skills'])
    project = Project(name=name, skills_set=skills, creator = ln_user)
    project.save()

    """ prepare object with connections and skills """
    li = LinkedIn(settings.LINKEDIN_CONSUMER_KEY,\
      settings.LINKEDIN_CONSUMER_SECRET)
    access_token = request.session['access_token']
    connections = li.connections_api.getMyConnections(access_token)
    members = []

    for conn in connections:
      member = Member()
      member.proj = project
      member.linkedin_url = conn.profile_url
      member.pic = conn.picture_url
      member.first_name = conn.firstname
      member.last_name = conn.lastname
      member.info = {}
      member.info['summary'] = conn.summary.lower()
      member.info['specialties'] = conn.specialties.lower()
      members.append(member)
      
    request.session['members_' + str(project.id)] = members

    return redirect('web.views.project', project.id)
  return render_to_response('project/create.html', {}, RequestContext(request))

def project_edit(request, id):
  name = request.POST['name']
  skills = extract_skills_from_user_string(request.POST['skills'])    
  project = Project.objects.get(pk=id)
  project.skills_set=skills
  project.name=name
  project.save()
  return render_to_response('project/edit.html', {}, RequestContext(request))

def project_delete(request, id):
  project = Project.objects.get(pk=id)
  project.delete()
  return redirect('web.views.dashboard')


def ajax_suggestions(request):
  project = Project.objects.get(pk=request.GET['project_id'])
  skills = project.skills_set
  members = request.session['members_' + str(project.id)]
  for member in members:
    update_skills_for_member(project, member)
    print member.skills_set
  return render_to_response('ajax/suggestions.html', {}, RequestContext(request))
