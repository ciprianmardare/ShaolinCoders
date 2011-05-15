from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from socialauth.models import LinkedInUserProfile
from web.helpers import extract_skills_from_user_string, get_skills_info, \
  update_skills_for_member, compute_score, build_member_data, get_github_profile
from web.models import Project, Member
import yql

def get_linkedin_user(request):
  ln_user_id = request.user.username[3:]
  return LinkedInUserProfile.objects.get(linkedin_uid = ln_user_id)

def index(request):
  logged_in = request.user.is_authenticated()
  if logged_in == False:
    return render_to_response('index.html', {'logged_in' : logged_in,})
  else:
    return redirect('web.views.dashboard')

def dashboard(request):
  ln_user = get_linkedin_user(request)
  if 'picture_url' not in request.session:
    request.session['picture_url'] = ln_user.profile_image_url
  projects = Project.objects.filter(creator = ln_user)
  for project in projects:
    member_list = Member.objects.filter(proj = project)
    project.skills_info = get_skills_info(project)
    project.members = member_list
  
  d = {'projects': projects}
  return render_to_response('dashboard.html', d, RequestContext(request))

def project(request, id):
  project = Project.objects.get(pk=id)

  if 'members_' + str(project.id) not in request.session:
    members = build_member_data(project, request.session['access_token'])
    request.session['members_' + str(project.id)] = members

  return render_to_response('project/project.html', { 'project': project}, RequestContext(request))

def project_create(request):
  if request.method == 'POST':
    ln_user = get_linkedin_user(request)
    name = request.POST['name']
    #skills = extract_skills_from_user_string(request.POST['skills'])
    #project = Project(name=name, skills_set=skills, creator = ln_user)
    project = Project(name=name, creator = ln_user)
    project.save()

    """ prepare object with connections and skills """
    members = build_member_data(project, request.session['access_token'])
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
  return render_to_response('project/edit.html',{}, RequestContext(request))

def ajax_score(request):
  project = Project.objects.get(pk=request.GET['project_id'])
  score = compute_score(project)*100
  return render_to_response('ajax/score.html', {'score' : score}, RequestContext(request))

def project_delete(request, id):
  project = Project.objects.get(pk=id)
  project.delete()
  return redirect('web.views.dashboard')

def url_not_in(url, members):
  for member in members:
    if url == member.linkedin_url:
      return False
  return True

def ajax_suggestions(request):
  project = Project.objects.get(pk=request.GET['project_id'])
  db_members = Member.objects.filter(proj=project)

  sets = project.skills_set
  if sets and len(sets) > 0:
    members = request.session['members_' + str(project.id)]

    new_members = [member for member in members if\
        url_not_in(member.linkedin_url, db_members) ]

    count = request.GET.get('count', 5)

    for member in new_members:
      update_skills_for_member(project, member)

    def score_calculator(member):
      return compute_score(project, member)
    results = sorted(new_members, key=score_calculator, reverse=True)[:count]
  else:
    results = []
  return render_to_response('ajax/suggestions.html', {'results':results}, RequestContext(request))

def ajax_members(request):
    project = Project.objects.get(pk=request.GET['project_id'])
    members = Member.objects.filter(proj=project)

    return render_to_response('ajax/members.html', {'results' : members},\
        RequestContext(request))

def member_add(request):
  # get member info from session
  idem_member = Member()
  project = Project.objects.get(pk = request.GET['project_id'])
  all_members = request.session['members_' + str(project.id)]
  for member in all_members:
    if member.linkedin_url == request.GET['url']:
      # add member to database
      idem_member.proj = project
      idem_member.linkedin_url = member.linkedin_url
      idem_member.first_name = member.first_name
      idem_member.last_name = member.last_name
      idem_member.pic = member.pic
      idem_member.info = member.info
      update_skills_for_member(project, idem_member)
      idem_member.save()
      break

  # update project score
  score = compute_score(project)
  project.score = score
  project.nr_members = project.nr_members + 1
  project.save()
  return HttpResponse('')

def member_delete(request):
  project = Project.objects.get(pk = request.GET['project_id'])
  member = Member.objects.get(proj = project,\
      linkedin_url = request.GET['url'])
  member.delete()
  return HttpResponse('')

def ajax_profiles(request):
  linkedin_profile = request.GET['linkedin_profile']

  github_profile = cache.get(linkedin_profile)
  if github_profile is None:
    github_profile = get_github_profile(linkedin_profile)
    if github_profile is None:
      github_profile = ''
    cache.set(linkedin_profile, github_profile)

  return HttpResponse(github_profile)

def page_not_found(request):
  y = yql.Public()
  response = y.execute('select * from flickr.photos.search where tags="openhackeu"')
  photos = response['query']['results']['photo']
  
  return render_to_response('404.html', {'photos':photos}, RequestContext(request))
