### Feature Ideas / Ideas for Improvement

---

The label Linkbase should have the functionality to get all labels for a given concept!
Currently you need a for loop to get a label. O(n) complexity!

```python
for locator in linkbase.extended_links[0].root_locators:
    if locator.concept_id != 'ifrs-full_Assets': continue
    # Here you have the label
    label: str = locator.children[0].labels[0].text
```
The access to the content of the label is also very cumbersome.

---

Allow parsing of xbrl documents without supplying a cache.
Sometimes you just want to parse ONE document without worrying about caching xbrl files. 

---

Parsing of Reference Linkbases

---