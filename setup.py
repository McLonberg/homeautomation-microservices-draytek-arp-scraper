import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="draytek_arp_cacher_dolphsps",
    version="0.0.2",
    author="Andreas Lonberg",
    author_email="andreas.lonberg@gmail.com",
    description="Draytek ARP Cacher for HomeAssistant.io presence detection.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Dolphsps/McLonberg.net",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)