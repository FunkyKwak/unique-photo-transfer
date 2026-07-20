import os
import shutil



def copy_file(source, destination):

    folder = os.path.dirname(destination)

    os.makedirs(
        folder,
        exist_ok=True
    )


    shutil.copy2(
        source,
        destination
    )