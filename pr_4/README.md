А - Скачування файлів з FTP серверу
1) Підключитися до FTP серверу: ftp.ubuntu.com
2) Перейти до каталогу ubuntu/dists/
3) Отримати зміст каталогу ubuntu/dists/ та зберегти його в файл на локальний диск: . ./downloads/ubuntudists.txt
4) Завантажити на локальний диск файл маніфесту (MANIFEST) для всіх доступних оновлень (bionic-updates, trusty-updates, xenial-updates, ...)
Наприклад, для trusty-updates повний шлях до файлу MANIFEST: ubuntu/dists/trusty-updates/main/mstaller-i386/20101020ubuntu318.46/images/ MANIFEST
Зміст trusty-updates MANIFEST:
■ MANIFEST - Блокнот
Файл Правка Формат Вид Справка
|cdrom-xen/cdroiii/xen/initrd,gz
cdrom-xen/cdrom/xen/vmlinuz
cdrom-xen/cdrom/xen/xm-debian.і
cdrom/debian-cd_info.tar,gz
cdrom/initrd.gz
cdrom/vmlinuz
hd-media/boot.img.gz
hd-media/initrd.gz
hd-media/wmlinuz
netboot/boot.img.g2
initrd for installing under xen
• kernel image for installing under Xen
• example Xen configuration isolinux config files for CD
■ initrd for use with isolinux to build a CD kernel for use with isolinux to build a CD
• 800 mb image (compressed) for USB memory stick for use on USB memory sticks
■ for use on USB memory sticks
• compressed network install image for USB memory stick
Б - Завантаження файлів на FTP сервер Бекап файлів звіту
На локальному диску розміщено каталог ZVIT з набором звітних файлі у форматі txt, docx, pdf. Розробити програмний додаток для автоматизації створення бекапу звітів за поточну добу. Бекап зберігається на FTP сервері в каталозі /data/arc/
1) Виконати аналіз каталогу ZVIT на наявність звітних матеріалів за поточну добу
2) Створити в каталозі FTP ARC файл, що містить назви звітних файлів за поточну добу та їх хеш код, формат назви файлу yyyy_mm_dd_hh_mm_ss
3) Підключитися до FTP сервера
4) Перейти на FTP сервері до каталогу /data/arc/
5) Створити в /data/arc/ каталог для бекапу звітних файлів за поточну добу, назва каталогу поточна дата у форматі yyyy_mm_dd
6) Завантажити на FTP сервер всі файли з каталогу ZVIT у яких поточна дата створення/оновлення
7) Розірвати з’єднання
Примітка. При неможливості використання безкоштовного FTP сервера використати умовні дані у якості параметрів FTP, та пояснити роботу програмного додатку без демонстрації підключення до FTP сервера.
 
Оформити протокол з відображенням завдання, коду клієнта та сервера, відображення усіх консолях, де працював код та висновки.