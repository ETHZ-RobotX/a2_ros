from setuptools import find_packages, setup

package_name = "a2_object_detection"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="your_name",
    maintainer_email="your_email@example.com",
    description="Object detection package",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "artifact_memory_node = a2_object_detection.artifact_memory_node:main",
        ],
    },
)
