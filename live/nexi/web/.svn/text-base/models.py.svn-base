from django.db import models
from socialauth.models import LinkedInUserProfile


def get_skills(obj):
  if obj._skills_set is None or len(obj._skills_set) == 0:
    return set()
  return obj._skills_set.split(',')

def set_skills(obj, skills):
  skills = (skill.lower() for skill in skills)
  obj._skills_set = ','.join(skills)

class Project(models.Model):
  name = models.CharField(max_length=128)
  creator = models.ForeignKey(LinkedInUserProfile, null=True)
  score = models.FloatField(default=0)
  _skills_set = models.CharField(max_length=1024, null=True, db_column='skills_set')
  nr_members = models.IntegerField(default=0)
  
  skills_set = property(get_skills, set_skills)

  def __unicode__(self):
    return self.name

class Member(models.Model):
  proj = models.ForeignKey('Project')
  linkedin_url = models.URLField(max_length=1024, null=True)
  _skills_set = models.CharField(max_length=1024, null=True,  db_column='skills_set')
  pic = models.URLField(max_length=1024, null=True)
  username = models.CharField(max_length=1024, null=True)
  first_name = models.CharField(max_length=1024, null=True)
  last_name = models.CharField(max_length=1024, null=True)
  
  skills_set = property(get_skills, set_skills)
