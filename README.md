# pdf_image_description_extraction
一、环境和用法

    Windows系统下以管理员身份打开Visual Studio
  
    import fitz库，pdf所在文件夹对应pdfdir，输出文件夹对应imgpath，更改后运行
  
二、主要功能

    extract_image_from_pages遍历pdfdir文件夹，把pdfdir下所有pdf中的图片和图片描述按页提取到imgpath文件夹下，过滤了前10页和小于2K的图片
  
  ![image](https://github.com/grandcyw/pdf_image_description_extraction/assets/129830047/3597daa4-36db-4489-b909-00965bc6831d)
![image](https://github.com/grandcyw/pdf_image_description_extraction/assets/129830047/84b91db2-5b38-4638-adae-4d474c7974a8)

    make_dataset.py做成数据集，key—value存储
