# Оценка проекта до взятия в работу
## 1. Потенциал проекта. Важность решения задачи.
**Проблема:** число камер видеонаблюдения, устанавливаемых на территории современных общественных заведений, может быть слишком велико, чтобы ручной анализ видео данных оставался эффективным.

Существуют задачи поиска объектов на видео данных, в которых нет чётко заданных времени или места поиска. Например:
- Поиск пропавших детей, домашних животных
- Поиск крупных забытых вещей
- Поиск всех появлений человека, совершившего правонарушение

Для их ручного решения требуется просматривать видео данные с множества камер или видео данные за длительные период времени. К примеру, в крупном торговом центре может быть расположено более 110 камер видеонаблюдения, записи с которых должны хранится не менее 30 дней.

Ручной поиск необходимых участков видео в таком объёме данных требует времени. Что само по себе может быть критично (например, в случае с пропавшим ребёнком), или может привести к тому, что решение задачи будет отложено на потом или вовсе отменено (например, в случае с поиском пропавшего рюкзака).

Автоматизированная система поиска, решающая эту задачу с большей скоростью, позволит решить эти проблемы.

**Востребованность:** задача поставлена лабораторией компании IVA Technologies в НИЯУ МИФИ.

## 2. Простые решения задачи.
Единственное простое решение задачи - ручной поиск целевых объектов в базе видео данных. Главным недостатком такого подхода является высокая временная сложность.

Задачи поиска конкретных людей можно решить, используя системы распознавания лиц. Однако такие системы неэффективны, если лицо человека закрыто другим объектом, или если изображения лица человека имеет недостаточно высокое разрешение.

## 3. Реалистичность решения проблемы с помощью машинного обучения.
Задача поиска объектов на видео по запросу на естественном языке, *video retrieval* - одна из современных задач машинного обучения.

В этом проекте требуется решить задачу поиска объектов, а не действий совершаемых ими или с ними, поэтому задачу video retrieval можно свести к задаче image retrieval, работая с видео покадрово.

Этой задаче посвящено [множество датасетов и архитектур решения](https://paperswithcode.com/task/image-retrieval), позволяющих решать её с высокой точностью.

Проблемой может стать недостаточно высокая скорость работы image retrieval систем. Однако, решением этой проблемы может стать дистилляция.

## 4. Технические требования.
Решение должно иметь достаточно высокую скорость работы, чтобы успевать индексировать данные, поступающие с камер видеонаблюдения, в реальном времени.

**Оценка нагрузки:** если заведение имеет на своей территории 150 камер, и индексируется один кадр на каждую секунду видео, то система должна иметь скорость индексирования порядка 150 изображений в секунду.

Индексация текстового запроса и поиск наиболее релевантных кадров производится только при обращении к системе оператора, поэтому на эти элементы решения ложиться меньшая нагрузка. Однако, для эффективной работы системы, они должны иметь достаточно высокую скорость обработки запросов. (Порядка нескольких минут)