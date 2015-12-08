import mock

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.importlib import import_module
from django.core.urlresolvers import reverse_lazy
from django.core.files import File
from django.contrib.messages.storage.fallback import FallbackStorage

from photoapp.models import FacebookUser, Photo
from photoapp.views import FacebookLogin, PhotoAppView,\
    EditPhotoView, DeletePhotoView


class UserSetupTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user1 = User.objects.create(
            first_name='John',
            last_name='doe',
            username='Johndoe',
            email='johndoe@doe.com')
        self.facebook_user1 = FacebookUser.objects.create(
            facebook_id=1,
            contrib_user=self.user1)

        self.data = {
            'first_name': 'andela',
            'last_name': 'andela',
            'email': 'email@email.com',
            'id': 2,
            'picture[data][url]': 'https://fbkamaihd.net/hprofile'
        }

        self.photo = Photo.objects.create(title='title')


class UserActionTestCase(UserSetupTestCase):

    def test_non_existing_user_login(self):

        request = self.factory.post('/photo/login/', self.data)
        engine = import_module(settings.SESSION_ENGINE)
        session_key = None
        request.session = engine.SessionStore(session_key)

        # assert that user loggedIn successfully
        response = FacebookLogin.as_view()(request)
        self.assertEquals(response.status_code, 200)

    def test_existing_user_login(self):
        data = {
            'first_name': 'John',
            'last_name': 'doe',
            'email': 'johndoe@doe.com',
            'id': 1,
            'picture[data][url]': 'https://fbkamdsaihd.net/hprofile'
        }
        request = self.factory.post('/photo/login/', data)
        engine = import_module(settings.SESSION_ENGINE)
        session_key = None
        request.session = engine.SessionStore(session_key)
        response = FacebookLogin.as_view()(request)
        self.assertEquals(response.status_code, 200)

    def test_model_creation(self):

        # assert that user does not exist in the database
        facebook_user2 = FacebookUser.objects.filter(id=2)
        self.assertEqual(len(facebook_user2), 0)

        # assert that user was successfully created and saved in db
        user2 = User.objects.create(username=self.data['first_name'],
                                    email=self.data['email'])
        facebook_user2 = FacebookUser.objects.create(
            facebook_id=self.data['id'], contrib_user=user2)
        facebook_user2 = FacebookUser.objects.filter(id=2)
        self.assertEqual(len(facebook_user2), 1)

    def test_user_signout(self):

        response = self.client.get(reverse_lazy('signout'))
        self.assertEquals(response.status_code, 302)

    def test_user_view_homepage(self):

        response = self.client.get(reverse_lazy('homepage'))
        self.assertEquals(response.status_code, 200)

    def test_user_view_photopage(self):
        request = self.factory.get(reverse_lazy('photoview'))
        request.user = self.user1
        response = PhotoAppView.as_view()(request)
        self.assertEquals(response.status_code, 200)


class TestPhotoUpload(UserSetupTestCase):

    @mock.patch('photoapp.models.Photo.save', mock.MagicMock(name="save"))
    def test_photo_upload_and_save(self):

        mock_file = mock.MagicMock(spec=File, name='FileMock')
        mock_file.name = 'testimage.jpg'
        request = self.factory.post(
            '/photoapp/photos/',
            data={'title': '', 'image': mock_file, })
        request.user = self.user1
        response = PhotoAppView.as_view()(request)
        self.assertEquals(response.status_code, 200)


class TestPhotoEdit(UserSetupTestCase):

    def test_editpage_view(self):

        request = self.factory.get('/photoshop/edit/')
        request.user = self.user1
        view = EditPhotoView.as_view()
        response = view(request, id=1, effects='default')
        self.assertEquals(response.status_code, 200)


class TestDeletePhoto(UserSetupTestCase):

    def test_delete_photo(self):

        with mock.patch('photoapp.views.DeletePhotoView.apidelete')\
                as mock_delete:

            mock_delete.return_value = (
                'deleted',
                {"deleted": {
                 "cb4eaaf650": "deleted", }
                 })

            request = self.factory.get('/photoshop/delete/')
            engine = import_module(settings.SESSION_ENGINE)
            session_key = None
            request.session = engine.SessionStore(session_key)
            messages = FallbackStorage(request)
            setattr(request, '_messages', messages)

            view = DeletePhotoView.as_view()
            response = view(request, id=1, public_id='xxyyzz')
            self.assertTrue(DeletePhotoView.apidelete.called)
            self.assertEquals(response.status_code, 302)

    def test_photo_not_deleted(self):

        with mock.patch('photoapp.views.DeletePhotoView.apidelete')\
                as mock_delete:

            mock_delete.return_value = (
                {"deleted": {
                 "cb4eaaf650": "deleted", }
                 }, 'deleted')

            request = self.factory.get('/photoshop/delete/')
            engine = import_module(settings.SESSION_ENGINE)
            session_key = None
            request.session = engine.SessionStore(session_key)
            messages = FallbackStorage(request)
            setattr(request, '_messages', messages)

            view = DeletePhotoView.as_view()
            response = view(request, id=1, public_id='xxyyzz')
            self.assertTrue(DeletePhotoView.apidelete.called)
            self.assertEquals(response.status_code, 302)
