import os

replacements = [
    ("from xsc_lib.xsc_lib_common.models.recognition import FaceTemplate, Person, ConsentStatus", "from xsc_lib.xsc_lib_common.models.recognition import FaceTemplate, Person, ConsentStatus"),
    ("from .models import Camera, CameraEvent", "from xsc_lib.xsc_lib_common.models.camera import Camera, CameraEvent"),
    ("from xsc_lib.xsc_lib_extn.ring import router as ring_router", "from xsc_lib.xsc_lib_app.api.routers import ring as ring_router"),
    ("from .models import", "from xsc_lib.xsc_lib_common.models.camera import"), # blanket fix for relative imports in camera_provider
]

for root, _, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            new_content = content
            for old, new in replacements:
                new_content = new_content.replace(old, new)
            
            # Additional targeted fixes
            new_content = new_content.replace("import xsc_lib.xsc_lib_extn.ring.router", "import xsc_lib.xsc_lib_app.api.routers.ring")
            
            # fix main.py
            if file == "main.py":
                new_content = new_content.replace("import xsc_lib.xsc_lib_app.api.routers as api_router", "from xsc_lib.xsc_lib_app.api import routers as api_router")
                new_content = new_content.replace("from xsc_lib.xsc_lib_app.api.routers import ring_router", "from xsc_lib.xsc_lib_app.api.routers.ring import router as ring_router")
                
            if new_content != content:
                with open(path, "w") as f:
                    f.write(new_content)
