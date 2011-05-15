from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings

import urllib
from socialauth.lib import oauthtwitter2 as oauthtwitter
from socialauth.models import OpenidProfile as UserAssociation, TwitterUserProfile, FacebookUserProfile, LinkedInUserProfile, AuthMeta
from socialauth.lib.linkedin import *

import random

TWITTER_CONSUMER_KEY = getattr(settings, 'TWITTER_CONSUMER_KEY', '')
TWITTER_CONSUMER_SECRET = getattr(settings, 'TWITTER_CONSUMER_SECRET', '')

FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', '')
FACEBOOK_API_KEY = getattr(settings, 'FACEBOOK_API_KEY', '')
FACEBOOK_SECRET_KEY = getattr(settings, 'FACEBOOK_SECRET_KEY', '')

# Linkedin
LINKEDIN_CONSUMER_KEY = getattr(settings, 'LINKEDIN_CONSUMER_KEY', '')
LINKEDIN_CONSUMER_SECRET = getattr(settings, 'LINKEDIN_CONSUMER_SECRET', '')

# OpenId setting map

OPENID_AX_PROVIDER_MAP = getattr(settings, 'OPENID_AX_PROVIDER_MAP', {})

class OpenIdBackend:
    def authenticate(self, openid_key, request, provider, user=None):
        try:
            assoc = UserAssociation.objects.get(openid_key = openid_key)
            return assoc.user
        except UserAssociation.DoesNotExist:
            #fetch if openid provider provides any simple registration fields
            nickname = None
            email = None
            firstname = None
            lastname = None
            
            if request.openid and request.openid.sreg:
                email = request.openid.sreg.get('email')
                nickname = request.openid.sreg.get('nickname')
                firstname, lastname = request.openid.sreg.get('fullname', ' ').split(' ', 1)
            elif request.openid and request.openid.ax:
                email = request.openid.ax.getSingle('http://axschema.org/contact/email')
                if 'google' in provider:
                    ax_schema = OPENID_AX_PROVIDER_MAP['Google']
                    firstname = request.openid.ax.getSingle(ax_schema['firstname'])
                    lastname = request.openid.ax.getSingle(ax_schema['lastname'])
                    nickname = email.split('@')[0]
                else:
                    ax_schema = OPENID_AX_PROVIDER_MAP['Default']
                    try:
                        nickname = request.openid.ax.getSingle(ax_schema['nickname']) #should be replaced by correct schema
                        firstname, lastname = request.openid.ax.getSingle(ax_schema['fullname']).split(' ', 1)
                    except:
                        pass

            if nickname is None :
                nickname =  ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for i in xrange(10)])
            
            name_count = User.objects.filter(username__startswith = nickname).count()
            if name_count:
                username = '%s%d' % (nickname, name_count + 1)
            else:
                username = '%s' % (nickname)
                
            if email is None :
                valid_username = False
                email =  "%s@socialauth" % (username)
            else:
                valid_username = True
            
            if not user:
                user = User.objects.create_user(username, email)
                
            user.first_name = firstname
            user.last_name = lastname
            user.save()
    
            #create openid association
            assoc = UserAssociation()
            assoc.openid_key = openid_key
            assoc.user = user
            if email:
                assoc.email = email
            if nickname:
                assoc.nickname = nickname
            if valid_username:
                assoc.is_username_valid = True
            assoc.save()
            
            #Create AuthMeta
            # auth_meta = AuthMeta(user=user, provider=provider, provider_model='OpenidProfile', provider_id=assoc.pk)
            auth_meta = AuthMeta(user=user, provider=provider)
            auth_meta.save()
            return user
        
    def GooglesAX(self,openid_response):
        email = openid_response.ax.getSingle('http://axschema.org/contact/email')
        firstname = openid_response.ax.getSingle('http://axschema.org/namePerson/first')
        lastname = openid_response.ax.getSingle('http://axschema.org/namePerson/last')
        # country = openid_response.ax.getSingle('http://axschema.org/contact/country/home')
        # language = openid_response.ax.getSingle('http://axschema.org/pref/language')
        return locals()
  
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk = user_id)
            return user
        except User.DoesNotExist:
            return None

class LinkedInBackend:
    """LinkedInBackend for authentication"""
    def authenticate(self, linkedin_access_token, user=None):
        linkedin = LinkedIn(LINKEDIN_CONSUMER_KEY, LINKEDIN_CONSUMER_SECRET)
        # get their profile
        
        profile = ProfileApi(linkedin).getMyProfile(access_token = linkedin_access_token)

        try:
            user_profile = LinkedInUserProfile.objects.get(linkedin_uid = profile.id)
            user = user_profile.user
            return user
        except LinkedInUserProfile.DoesNotExist:
            # Create a new user
            username = 'LI:%s' % profile.id

            if not user:
                user = User(username =  username)
                user.first_name, user.last_name = profile.firstname, profile.lastname
                user.email = '%s@socialauth' % (username)
                user.save()
                
            userprofile = LinkedInUserProfile(user=user, linkedin_uid=profile.id, profile_image_url=profile.picture_url)
            userprofile.save()
            
            auth_meta = AuthMeta(user=user, provider='LinkedIn').save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None

class TwitterBackend:
    """TwitterBackend for authentication"""
    def authenticate(self, twitter_access_token, user=None):
        '''authenticates the token by requesting user information from twitter'''
        # twitter = oauthtwitter.OAuthApi(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, twitter_access_token)
        twitter = oauthtwitter.TwitterOAuthClient(settings.TWITTER_CONSUMER_KEY, settings.TWITTER_CONSUMER_SECRET)
        try:
            userinfo = twitter.get_user_info(twitter_access_token)
        except:
            # If we cannot get the user information, user cannot be authenticated
            raise

        screen_name = userinfo.screen_name
        twitter_id = userinfo.id
        
        try:
            user_profile = TwitterUserProfile.objects.get(screen_name=screen_name)
            
            # Update Twitter Profile
            user_profile.url = userinfo.url
            user_profile.location = userinfo.location
            user_profile.description = userinfo.description
            user_profile.profile_image_url = userinfo.profile_image_url
            user_profile.save()
            
            user = user_profile.user
            return user
        except TwitterUserProfile.DoesNotExist:
            # Create new user
            if not user:
                same_name_count = User.objects.filter(username__startswith=screen_name).count()
                if same_name_count:
                    username = '%s%s' % (screen_name, same_name_count + 1)
                else:
                    username = screen_name
                user = User(username=username)
                name_data = userinfo.name.split()
                try:
                    first_name, last_name = name_data[0], ' '.join(name_data[1:])
                except:
                    first_name, last_name =  screen_name, ''
                user.first_name, user.last_name = first_name, last_name
                #user.email = screen_name + "@socialauth"
                #user.email = '%s@example.twitter.com'%(userinfo.screen_name)
                user.save()
                
            user_profile = TwitterUserProfile(user=user, screen_name=screen_name)
            user_profile.access_token = twitter_access_token
            user_profile.url = userinfo.url
            user_profile.location = userinfo.location
            user_profile.description = userinfo.description
            user_profile.profile_image_url = userinfo.profile_image_url
            user_profile.save()
            
            auth_meta = AuthMeta(user=user, provider='Twitter').save()
                
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None