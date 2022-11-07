import unittest

class Test(unittest.TestCase):
    def test(self):
        from xbrl.linkbase import parse_linkbase, LinkbaseType
        pre = r'D:\tifrs\tifrs-20200630\BSCI\tifrs-bsci-ci-2020-06-30-presentation.xml'
        pre = parse_linkbase(pre, linkbase_type=LinkbaseType.PRESENTATION)
        bal = pre.extended_links[0]
        print(bal.treeview())
        
        # from treelib import Tree
        # from treelib.exceptions import DuplicatedNodeIdError
        # t = Tree()
        # r = t.create_node('r', 'r')
        # def make_arc(arc, p):
        #     t.create_node(arc.to_locator.name, str(arc), p)
        #     for c_arc in arc.to_locator.children:
        #         make_arc(c_arc, str(arc))
        # for l in pre.extended_links:
        #     # breakpoint()
        #     t.create_node(l.role, l.elr_id, 'r')
        #     for loc in l.root_locators:
        #         t.create_node(loc.name, loc.href, l.elr_id)
        #         for arc in loc.children:
        #             make_arc(arc, loc.href)
        #             # t.create_node(arc.to_locator.name, str(arc), loc.href)
        # t.show()
        # # pl = tax.pre_linkbases
        # # for p in pl:
        #     # breakpoint()
        #     # print(p)


if __name__ == '__main__':
    unittest.main()
