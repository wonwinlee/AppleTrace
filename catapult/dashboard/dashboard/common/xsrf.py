# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Decorator that validates XSRF tokens."""

import os

from google.appengine.api import users
from google.appengine.ext import ndb

from oauth2client import xsrfutil


class XsrfSecretKey(ndb.Model):
  """Stores a secret XSRF key for the site."""
  token = ndb.StringProperty(indexed=False)


def _ValidateToken(token, user):
  """Validates an XSRF token generated by GenerateXsrfToken."""
  return xsrfutil.validate_token(
      _GetSecretKey(), token, user_id=user.user_id(), action_id='')


def GenerateToken(user):
  return xsrfutil.generate_token(
      _GetSecretKey(), user_id=user.user_id(), action_id='')


def _GenerateNewSecretKey():
  """Returns a random XSRF secret key."""
  return str(os.urandom(16).encode('hex'))


def _GetSecretKey():
  """Gets or creates the secret key to use for validating XSRF tokens."""
  key_entity = ndb.Key('XsrfSecretKey', 'site').get()
  if not key_entity:
    key_entity = XsrfSecretKey(id='site', token=_GenerateNewSecretKey())
    key_entity.put()
  return key_entity.token.encode('ascii', 'ignore')


def TokenRequired(handler_method):
  """A decorator to require that the XSRF token be validated for the handler."""

  def CheckToken(self, *args, **kwargs):
    user = users.get_current_user()
    token = str(self.request.get('xsrf_token'))
    if not user or not _ValidateToken(token, user):
      self.abort(403)
    handler_method(self, *args, **kwargs)

  return CheckToken
