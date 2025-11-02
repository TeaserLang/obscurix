# Cấu hình gói PyPI cho Obscurix

import setuptools

def read_file(filepath):
    """Đọc nội dung file để sử dụng trong setup."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

setuptools.setup(
    name='obscurix',
    version='0.1.0',
    author='Teaserverse',
    description="An esoteric programming language (esolang) designed for density and structural complexity.",
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    
    # Thiết lập điểm vào CLI (Entry Point)
    entry_points={
        # Khi người dùng gõ 'obscurix <file>', nó sẽ gọi obscurix.__main__.main()
        'console_scripts': [
            'obscurix = obscurix.__main__:main',
        ],
    },
)
