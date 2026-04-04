from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import json
import requests



# Simple Nepali translations for common legal terms
TRANSLATIONS = {
    'Civil Law': 'नागरिक कानुन',
    'Constitutional Law': 'संवैधानिक कानुन',
    'Criminal Law': 'फौजदारी कानुन',
    'Evidence Law': 'प्रमाण कानुन',
    'General': 'सामान्य',
    'Law Explorer': 'कानुन अन्वेषक',
    'Browse, search, and understand Nepal\'s legal documents': 'नेपालको कानुनी दस्तावेजहरू हेर्नुहोस्, खोज्नुहोस् र बुझ्नुहोस्',
    'Search laws...': 'कानुन खोज्नुहोस्...',
    'All Categories': 'सबै श्रेणीहरू',
    'Search': 'खोज्नुहोस्',
    'Clear': 'मेटाउनुहोस्',
    'Found': 'भेटियो',
    'matching': 'मिल्दो',
    'in': 'मा',
    'No laws found': 'कानुन भेटिएन',
    'Try adjusting your search criteria or browse all laws.': 'आफ्नो खोज मापदण्ड समायोजन गर्नुहोस् वा सबै कानुन हेर्नुहोस्।',
    'Clear Filters': 'फिल्टर मेटाउनुहोस्',
    'View Sections': 'धारा हेर्नुहोस्',
    'and': 'र',
    'more sections': 'थप धाराहरू',
    'Legal texts are provided for informational purposes only': 'कानुनी पाठहरू केवल सूचनात्मक उद्देश्यका लागि प्रदान गरिएका छन्',
    'may not reflect recent amendments': 'हालैका संशोधनहरू प्रतिबिंबित नहुन सक्छन्',
}


def get_translation(key, lang='en'):
    """Get translation for a key based on language"""
    if lang == 'np' and key in TRANSLATIONS:
        return TRANSLATIONS[key]
    return key


def parse_law_data(data, category):
    """Parse law data from JSON - handles both dict and list formats"""
    laws = []
    
    if isinstance(data, dict):
        # Check if it's a nested structure (chapters -> sections)
        has_chapters = False
        for key, value in data.items():
            if isinstance(value, dict):
                # Check if this looks like a chapter
                first_item = next(iter(value.values()), None)
                if first_item and isinstance(first_item, dict) and 'title' in first_item:
                    has_chapters = True
                    break
        
        if has_chapters:
            # Nested structure: Chapters -> Sections
            sections_list = []
            for chapter_key, chapter_data in data.items():
                if isinstance(chapter_data, dict):
                    for section_key, section_data in chapter_data.items():
                        if isinstance(section_data, dict):
                            sections_list.append({
                                'section_en': f"{section_key}: {section_data.get('title', '')}",
                                'content_en': section_data.get('content', ''),
                            })
            
            if sections_list:
                laws.append({
                    'title_en': category,
                    'summary_en': f"{category} contains {len(sections_list)} sections",
                    'category': category,
                    'sections': sections_list,
                })
        else:
            # Flat structure: directly sections
            for key, value in data.items():
                if isinstance(value, dict):
                    title = value.get('title', key)
                    content = value.get('content', '')
                    laws.append({
                        'title_en': title,
                        'summary_en': content[:200] if content else '',
                        'category': category,
                        'sections': [{'section_en': content[:500], 'content_en': content}] if content else []
                    })
    
    elif isinstance(data, list):
        # List format
        for item in data:
            if isinstance(item, dict):
                sections = item.get('sections', [])
                # Convert sections to proper format if needed
                formatted_sections = []
                for sec in sections:
                    if isinstance(sec, dict):
                        formatted_sections.append({
                            'section_en': sec.get('title_en', sec.get('title', '')),
                            'content_en': sec.get('content_en', sec.get('content', '')),
                        })
                    else:
                        formatted_sections.append({'section_en': str(sec), 'content_en': ''})
                
                laws.append({
                    'title_en': item.get('title', item.get('title_en', 'Unknown')),
                    'summary_en': item.get('summary_en', item.get('content', ''))[:200],
                    'category': item.get('category', category),
                    'sections': formatted_sections,
                })
                if item.get('category'):
                    pass  # Categories already handled
    
    return laws


def explorer(request):
    """
    Law Explorer page - requires authentication
    Loads from all JSON files in static/data folder
    """
    user = request.session.get('user')
    if not user:
        messages.warning(request, "Please log in to access the Law Explorer.")
        return redirect('login')
    
    # Load all JSON files from static/data
    static_data_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'data')
    json_files = ['Civil.json', 'Constitution.json', 'Criminal1.json', 'Criminal2.json', 'Criminal3.json', 'Evidence_Act.json']
    
    all_laws = []
    categories_set = set()
    
    for filename in json_files:
        filepath = os.path.join(static_data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Determine category from filename
                if 'Civil' in filename:
                    category = 'Civil Law'
                elif 'Constitution' in filename:
                    category = 'Constitutional Law'
                elif 'Criminal' in filename:
                    category = 'Criminal Law'
                elif 'Evidence' in filename:
                    category = 'Evidence Law'
                else:
                    category = 'General'
                
                categories_set.add(category)
                
                # Parse the law data
                laws = parse_law_data(data, category)
                all_laws.extend(laws)
                    
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    # Also try laws.json if it exists
    laws_file = os.path.join(static_data_dir, 'laws.json')
    if os.path.exists(laws_file):
        try:
            with open(laws_file, 'r', encoding='utf-8') as f:
                laws_data = json.load(f)
                for law in laws_data:
                    all_laws.append(law)
                    if law.get('category'):
                        categories_set.add(law['category'])
        except Exception as e:
            print(f"Error loading laws.json: {e}")
    
    laws = all_laws
    categories = sorted(categories_set)
    
    # Get search query and category filter from GET parameters
    query = request.GET.get('q', '').strip().lower()
    selected_category = request.GET.get('category', '').strip()
    
    # Filter laws
    filtered_laws = laws
    if query:
        filtered_laws = [law for law in filtered_laws 
                        if query in law.get('title_en', '').lower() 
                        or query in law.get('summary_en', '').lower()
                        or any(query in sec.get('section_en', '').lower() or query in sec.get('content_en', '').lower() for sec in law.get('sections', []))]
    
    if selected_category:
        filtered_laws = [law for law in filtered_laws if law.get('category') == selected_category]
    
    # Get language preference (default to English)
    lang = request.GET.get('lang', 'en')
    
    # Pre-compute translations for the current language
    ui_texts = {
        'title': get_translation('Law Explorer', lang),
        'subtitle': get_translation('Browse, search, and understand Nepal\'s legal documents', lang),
        'search_placeholder': get_translation('Search laws...', lang),
        'all_categories': get_translation('All Categories', lang),
        'search_btn': get_translation('Search', lang),
        'clear_btn': get_translation('Clear', lang),
        'found': get_translation('Found', lang),
        'matching': get_translation('matching', lang),
        'in': get_translation('in', lang),
        'no_results': get_translation('No laws found', lang),
        'no_results_desc': get_translation('Try adjusting your search criteria or browse all laws.', lang),
        'clear_filters': get_translation('Clear Filters', lang),
        'view_sections': get_translation('View Sections', lang),
        'and': get_translation('and', lang),
        'more_sections': get_translation('more sections', lang),
        'disclaimer': get_translation('Legal texts are provided for informational purposes only', lang),
        'disclaimer2': get_translation('may not reflect recent amendments', lang),
    }
    
    # Get pagination parameters
    page = request.GET.get('page', 1)
    per_page = 20  # Number of laws per page
    
    # Create paginator
    paginator = Paginator(filtered_laws, per_page)
    
    try:
        laws = paginator.page(page)
    except PageNotAnInteger:
        laws = paginator.page(1)
    except EmptyPage:
        laws = paginator.page(paginator.num_pages)
    
    # Load PDF data
    base_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs')
    pdf_data = {}
    
    # Loop through folders
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        
        if os.path.isdir(folder_path):
            pdf_files = []
            
            # Loop through files in each folder
            for file in os.listdir(folder_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append({
                        'name': file,
                        'path': f'pdfs/{folder}/{file}'
                    })
            
            pdf_data[folder] = pdf_files
    
    context = {
        'laws': laws,
        'paginator': paginator,
        'categories': categories,
        'query': request.GET.get('q', ''),
        'selected_category': selected_category,
        'lang': lang,
        'ui': ui_texts,
        'pdf_data': pdf_data,
    }
    return render(request, 'explorer/explorer.html', context)


# pdf


def pdf_list(request):
    base_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs')

    pdf_data = {}

    # Loop through folders
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)

        if os.path.isdir(folder_path):
            pdf_files = []

            # Loop through files in each folder
            for file in os.listdir(folder_path):
                if file.lower().endswith('.pdf'):
                    pdf_files.append({
                        'name': file,
                        'path': f'pdfs/{folder}/{file}'
                    })

            pdf_data[folder] = pdf_files

    return render(request, 'pdf_list.html', {'pdf_data': pdf_data})