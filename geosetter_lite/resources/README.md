# How to re-compile the Qt resource file

```sh
uv run pyside6-rcc geosetter_lite/resources/resources.qrc -o geosetter_lite/resources/resources_rc.py
```

This will generate file `resources_rc.py` (imported in `main.py`), with resources loaded using `qrc:///resources/leaflet/` prefix.
