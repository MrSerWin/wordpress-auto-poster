# 📂 Маппинг категорий

## Описание

Система автоматически мапит категории из CSV файлов на существующие категории портала.

## Маппинг категорий

| Исходная категория | Категория на портале |
|-------------------|---------------------|
| `Culture` | `AI & Culture` |
| `Society` | `AI & Society` |
| `Practice` | `AI Pro Tips / How-To` |
| `Innovation` | `Innovation` |
| `Review` | `Review` |
| `News` | `News` |
| `History` | `History` |
| `Video` | `Video` |

## Правила маппинга

1. **Точное совпадение** - если категория точно совпадает с существующей, она остается без изменений
2. **Маппинг по таблице** - категории мапятся согласно таблице выше
3. **По умолчанию** - если категория не найдена в маппинге, используется `News`

## Примеры маппинга

```
Culture → AI & Culture
Society → AI & Society  
Practice → AI Pro Tips / How-To
Innovation → Innovation (без изменений)
Review → Review (без изменений)
News → News (без изменений)
Unknown → News (по умолчанию)
```

## Текущая статистика

- **AI Pro Tips / How-To**: 6 статей
- **AI & Society**: 6 статей  
- **Innovation**: 5 статей
- **AI & Culture**: 4 статьи
- **Review**: 3 статьи
- **News**: 1 статья

## Добавление новых категорий

Чтобы добавить новую категорию в маппинг, обновите словарь `CATEGORY_MAPPING` в файле `load_csv_plan.py`:

```python
CATEGORY_MAPPING = {
    'Culture': 'AI & Culture',
    'Society': 'AI & Society', 
    'Practice': 'AI Pro Tips / How-To',
    'Innovation': 'Innovation',
    'Review': 'Review',
    'News': 'News',
    'History': 'History',
    'Video': 'Video',
    'NewCategory': 'New Portal Category'  # Добавить новую категорию
}
```

## Использование

Маппинг происходит автоматически при загрузке CSV файла:

```bash
python load_csv_plan.py plans/your_plan.csv
```

Система покажет маппинг в выводе:
```
✅ Строка 1: добавлена - 'Title...' (категория: Culture → AI & Culture)
✅ Строка 2: добавлена - 'Title...' (категория: Innovation)
```
