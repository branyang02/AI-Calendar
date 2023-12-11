#from django.test import TestCase
#from django.conf import settings
#from django.urls import reverse, resolve
#from main.utils.chatgpt import ChatGPT
#from django.test import SimpleTestCase
#from main.views import map, chat_endpoint
#
#class viewsTests(TestCase):

#    def test_map(self):
#        response = self.client.get(reverse('map'))
#        self.assertEqual(response.status_code, 200)
#        self.assertTemplateUsed(response, 'main/map.html')
#        self.assertIn('key', response.context)
#        self.assertEqual(response.context['key'], settings.GOOGLE_MAPS_API_KEY)

#    def test_chatgpt(self):
#        chat_real = ChatGPT()
#        test_message = 'test'
#        response = self.client.post(reverse('chat_endpoint'), {'message': test_message})
#        self.assertEqual(response.status_code, 200)
#        self.assertJSONEqual(str(response.content, encoding='utf-8'), {'response': chat_real.query_message(test_message)})


#class URLTests(SimpleTestCase):

#    def test_mapURL(self):
#        url = reverse('map')
#        self.assertEquals(resolve(url).func, map)



#    def test_chatURL(self):
#          url = reverse('chat_endpoint')
#          self.assertEquals(resolve(url).func, chat_endpoint)
