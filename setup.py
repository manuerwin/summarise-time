import setuptools as sut

sut.setup(
    name="Summarise activities",
    version="1.2.0",
    description="Python app - process and summarise activity lines from CSV",
    author="Manu Erwin",
    packages=sut.find_packages(),
    python_requires="==3.13",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    include_package_data=True,
)
