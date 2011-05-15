from django.conf import settings
from socialauth.lib.linkedin import LinkedIn
from web.models import Member
import re
import yql


y = yql.Public()
YQL_ENV = "store://datatables.org/alltableswithkeys"
GITHUB_TYPE = 'http:__github.com_'
GOOGLE_TYPE = 'http:__profiles.google.com_'


def extract_skills_from_user_string(text):
  return set(re.findall(r'[\+_\-#\*A-Za-z0-9]+', text))

def update_skills_for_member(project, member):
  project_skills = project.skills_set
  skills = set()
  text = ' '.join(member.info.values())
  for skill in project_skills:
    if skill in text:
      skills.add(skill)
  member.skills_set = skills

def compute_score(project, member=None):
  proj_skills = get_skills_info(project)

  if member:
    # fill project skills [2,1,0,1,0,...] with member skills
    member_skills = member.skills_set
    for skill in member_skills:
      proj_skills[skill] += 1

  # calculate number of matched skills so far
  count = len([x for x in proj_skills.values() if x > 0])

  # calculate score
  score = float(count)/len(proj_skills) if len(proj_skills) > 0 else 0
  return score

def get_skills_info(project):
  members = Member.objects.filter(proj=project.id)

  project_skills = project.skills_set
  skills_info = dict((x,0) for x in project_skills if len(x) > 0)

  for member in members:
    member_skills = member.skills_set
    for skill in member_skills:
      skills_info[skill] += 1

  return skills_info

def build_member_data(project, access_token):
  li = LinkedIn(settings.LINKEDIN_CONSUMER_KEY,\
      settings.LINKEDIN_CONSUMER_SECRET)
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

  return members

def get_github_profile(linkedin_profile):
  query = 'SELECT * FROM google.socialgraph.lookup WHERE fme=1 AND edi=1 AND q=\'%s\'' % linkedin_profile
  result = y.execute(query, env=YQL_ENV)
  github_profile = _get_profile(result, GITHUB_TYPE)
  if not github_profile:
    google_profile = _get_profile(result, GOOGLE_TYPE)
    if google_profile:
      github_profile = _get_github_profile_from_google(google_profile)
  return github_profile

def _get_profile(query_result, profile_type):
  count = query_result['query']['count']
  if count > 0:
    nodes = query_result['query']['results']['json']['nodes']
    for node in nodes.values():
      ref_nodes = node.get('nodes_referenced_by')
      if ref_nodes:
        for ref_node in ref_nodes:
          u = ref_node.replace(profile_type, '')
          if not u == ref_node:
            return profile_type.replace('_', '/') + u
  
  return None

def _get_github_profile_from_google(google_profile):
  query = 'SELECT * FROM google.socialgraph.lookup WHERE fme=1 AND q=\'%s\'' % google_profile
  result = y.execute(query, env=YQL_ENV)
  
  count = result['query']['count']
  if count > 0:
    nodes = result['query']['results']['json']['nodes']
    for node in nodes.keys():
      u = node.replace(GITHUB_TYPE, '')
      if not u == node:
        return GITHUB_TYPE.replace('_', '/') + u
  
  return None
