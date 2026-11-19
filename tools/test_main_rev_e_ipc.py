#!/usr/bin/env python3
"""Focused negative tests for the exact IPC-D-356 no-connect alias policy."""
import copy
import unittest
from check_main_rev_e_gerbers import ipc_pin_review


class IpcPinReviewTests(unittest.TestCase):
    def setUp(self):
        self.source={'sheets':[{'components':[
            {'ref':'U2','pins':[{'num':'2','name':'VIN','net':'+5V'},
                               {'num':'8','name':'PG','net':None}]},
            {'ref':'U3','pins':[{'num':'4','name':'NC','net':None}]}]}]}
        self.pins=[{'ref':'U2','pin':'2','net':'+5V'},
                   {'ref':'U2','pin':'8','net':''}, {'ref':'U3','pin':'4','net':''}]
        self.actual={('U2','2'):{'+5V'},('U2','8'):{'unconnected-(U2-PG-Pad8)'},
                     ('U3','4'):{'unconnected-(U3-NC-Pad4)'}}

    def review(self):
        return ipc_pin_review(self.pins,self.source,self.actual)

    def test_exact_same_pad_aliases_pass(self):
        result=self.review()
        self.assertFalse(result['pin_net_differences'])
        self.assertFalse(result['unexpected_pins'])
        self.assertEqual(len(result['normalized_nc_aliases']),2)

    def test_another_nc_pad_alias_is_rejected(self):
        self.actual['U2','8']={'unconnected-(U3-NC-Pad4)'}
        self.assertEqual(self.review()['pin_net_differences'][0]['pin'],'8')

    def test_nc_connected_to_real_net_is_rejected(self):
        self.actual['U2','8']={'GND'}
        self.assertTrue(self.review()['pin_net_differences'])

    def test_missing_nc_record_is_rejected(self):
        del self.actual['U2','8']
        self.assertTrue(self.review()['pin_net_differences'])

    def test_mixed_nc_record_names_are_rejected(self):
        self.actual['U2','8'].add('N/C')
        self.assertTrue(self.review()['pin_net_differences'])

    def test_connected_pin_cannot_use_nc_alias(self):
        self.actual['U2','2']={'unconnected-(U2-VIN-Pad2)'}
        self.assertTrue(self.review()['pin_net_differences'])

    def test_unexpected_pin_is_rejected(self):
        self.actual['U2','99']={'GND'}
        self.assertEqual(self.review()['unexpected_pins'],[('U2','99')])

    def test_different_source_inventory_is_rejected(self):
        self.pins[0]['net']='GND'
        with self.assertRaises(ValueError):
            self.review()

    def test_duplicate_inventory_pin_is_rejected(self):
        self.pins.append(copy.deepcopy(self.pins[0]))
        with self.assertRaises(ValueError):
            self.review()


if __name__=='__main__':
    unittest.main()
