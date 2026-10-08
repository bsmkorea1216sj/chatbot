import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
from fastapi.testclient import TestClient
import app as service
from research import references

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(service.app)
    def tearDown(self):
        service.app.dependency_overrides.clear()

    def test_private_routes_require_login(self):
        self.assertEqual(self.client.get('/api/account').status_code,401)
        self.assertEqual(self.client.get('/api/research/'+'a'*64).status_code,401)
        self.assertEqual(self.client.post('/internal/work',json={'job_id':'a'*64}).status_code,401)

    def test_ui_and_public_config_hide_costs(self):
        self.assertEqual(self.client.get('/').status_code,200)
        config=self.client.get('/api/config').json()
        self.assertFalse(config['payments_connected'])
        self.assertNotIn('spent',config)
        self.assertNotIn('granted',config)

    def test_google_provider_required(self):
        with patch.object(service,'firebase_app',return_value=None),patch.object(
            service.auth,'verify_id_token',return_value={'uid':'u','email_verified':True,
                'firebase':{'sign_in_provider':'password'}}):
            self.assertEqual(self.client.get('/api/account',headers={'Authorization':'Bearer test'}).status_code,401)

    def test_source_validation_and_price_fail_closed(self):
        service.app.dependency_overrides[service.user]=lambda:'u'
        payload={'request_id':'abcdefghijklmnop','topic':'AI research',
                 'categories':['unsupported']}
        self.assertEqual(self.client.post('/api/research',json=payload).status_code,422)
        payload['categories']=['논문']
        with patch.object(service,'quote',side_effect=KeyError('PRICE_VERSION')):
            self.assertEqual(self.client.post('/api/research',json=payload).status_code,503)

    def test_report_ownership(self):
        service.app.dependency_overrides[service.user]=lambda:'u'
        snapshot=NS(to_dict=lambda:{'uid':'someone_else','report':'private'})
        fake=NS(collection=lambda _:NS(document=lambda _:NS(get=lambda:snapshot)))
        with patch.object(service,'db',return_value=fake):
            r=self.client.get('/api/research/'+'a'*64)
            self.assertEqual(r.status_code,404)
            self.assertNotIn('private',r.text)

    def test_korean_citation_byte_positions(self):
        text='한국어 사실입니다.'
        meta=NS(grounding_chunks=[NS(web=NS(uri='https://example.org/paper',title='논문'))],
            grounding_supports=[NS(segment=NS(end_index=len(text.encode())),
                                   grounding_chunk_indices=[0])],search_entry_point=None)
        response=NS(text=text,candidates=[NS(finish_reason='STOP',grounding_metadata=meta)])
        output=references(response)
        self.assertIn(text+' [1]',output['report'])
        self.assertIn('참고문헌',output['report'])

    def test_no_grounding_rejected(self):
        with self.assertRaises(ValueError):
            references(NS(text='Unverified',candidates=[NS(finish_reason='STOP',grounding_metadata=None)]))

if __name__=='__main__': unittest.main()
