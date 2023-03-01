import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="jaspice",  # Replace with your own username
    version="0.0.1",
    install_requires=[
        "fastapi==0.87.0",
        "graphviz==0.20.1",
        "joblib==1.2.0",
        "matplotlib==3.6.1",
        "networkx==2.8.8",
        "numpy==1.23.2",
        "pexpect==4.8.0",
        "Pillow==9.3.0",
        "pycocoevalcap==1.2",
        "pydantic==1.8.2",
        "pyknp==0.6.1",
        "ray==2.0.0",
        "requests==2.28.1",
        "tqdm==4.64.0",
        "uvicorn==0.19.0"
    ],
    author="Yuiga Wada",
    author_email="yuigawada@gmail.com",
    description="Evaluation code for machine-generated image captions in Japanese.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/keio-smilab23/JaSPICE",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    license='BSD-3-Clause-Clear',
    python_requires='>=3.6'
)
