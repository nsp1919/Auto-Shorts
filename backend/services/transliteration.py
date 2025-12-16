"""
Telugu to Roman Telugu Transliteration Service
Converts Telugu script to English letters with phonetic pronunciation
Used for Instagram Reels & YouTube Shorts style captions
"""

import re

# Telugu vowels and their Roman equivalents
VOWELS = {
    'అ': 'a', 'ఆ': 'aa', 'ఇ': 'i', 'ఈ': 'ee', 'ఉ': 'u', 'ఊ': 'oo',
    'ఎ': 'e', 'ఏ': 'e', 'ఐ': 'ai', 'ఒ': 'o', 'ఓ': 'o', 'ఔ': 'au',
    'ృ': 'ru', 'ౄ': 'roo'
}

# Telugu vowel marks (matras)
VOWEL_MARKS = {
    'ా': 'aa', 'ి': 'i', 'ీ': 'ee', 'ు': 'u', 'ూ': 'oo',
    'ె': 'e', 'ే': 'e', 'ై': 'ai', 'ొ': 'o', 'ో': 'o', 'ౌ': 'au',
    'ృ': 'ru', '్': ''  # Virama - removes inherent vowel
}

# Telugu consonants and their Roman equivalents
CONSONANTS = {
    'క': 'ka', 'ఖ': 'kha', 'గ': 'ga', 'ఘ': 'gha', 'ఙ': 'nga',
    'చ': 'cha', 'ఛ': 'chha', 'జ': 'ja', 'ఝ': 'jha', 'ఞ': 'nya',
    'ట': 'ta', 'ఠ': 'tha', 'డ': 'da', 'ఢ': 'dha', 'ణ': 'na',
    'త': 'tha', 'థ': 'tha', 'ద': 'da', 'ధ': 'dha', 'న': 'na',
    'ప': 'pa', 'ఫ': 'pha', 'బ': 'ba', 'భ': 'bha', 'మ': 'ma',
    'య': 'ya', 'ర': 'ra', 'ల': 'la', 'వ': 'va', 'శ': 'sha',
    'ష': 'sha', 'స': 'sa', 'హ': 'ha', 'ళ': 'la', 'క్ష': 'ksha',
    'ఱ': 'rra', 'ం': 'n', 'ః': 'h', 'ఁ': 'n'
}

# Common Telugu words with their preferred Roman spellings (for accuracy)
COMMON_WORDS = {
    'ఏమి': 'emi',
    'ఏమైంది': 'emaindi',
    'ఎం': 'em',
    'నువ్వు': 'nuvvu',
    'నేను': 'nenu',
    'మీరు': 'meeru',
    'ఎక్కడ': 'ekkada',
    'ఉన్నావ్': 'unnav',
    'ఉన్నాడు': 'unnadu',
    'ఉన్నది': 'unnadi',
    'చేస్తున్నావ్': 'chestunnav',
    'చేస్తున్నాను': 'chestunnanu',
    'వీడియో': 'video',
    'చూసావా': 'choosava',
    'చూడు': 'choodu',
    'రా': 'ra',
    'రండి': 'randi',
    'అవును': 'avunu',
    'కాదు': 'kaadu',
    'ఎందుకు': 'enduku',
    'ఇక్కడ': 'ikkada',
    'అక్కడ': 'akkada',
    'ఇప్పుడు': 'ippudu',
    'అప్పుడు': 'appudu',
    'బాగుంది': 'bagundi',
    'బాగోలేదు': 'bagoledu',
    'తెలుసు': 'telusu',
    'తెలియదు': 'teliyadu',
    'వచ్చాను': 'vacchanu',
    'వెళ్ళాను': 'vellanu',
    'పోదాం': 'podam',
    'తినాలి': 'tinali',
    'చెప్పు': 'cheppu',
    'వినండి': 'vinandi',
}


def transliterate_telugu_to_roman(text: str) -> str:
    """
    Convert Telugu script to Roman Telugu (English letters).
    Preserves the phonetic pronunciation for Instagram/YouTube style captions.
    """
    if not text:
        return ""
    
    # Check if text contains Telugu characters
    if not any('\u0C00' <= char <= '\u0C7F' for char in text):
        return text  # Not Telugu, return as-is
    
    result = []
    words = text.split()
    
    for word in words:
        # Check common words first
        if word in COMMON_WORDS:
            result.append(COMMON_WORDS[word])
            continue
        
        # Check word without trailing punctuation
        word_clean = word.rstrip('?!.,')
        if word_clean in COMMON_WORDS:
            result.append(COMMON_WORDS[word_clean])
            continue
        
        # Transliterate character by character
        roman_word = ""
        i = 0
        while i < len(word):
            char = word[i]
            
            # Check if it's a Telugu character
            if '\u0C00' <= char <= '\u0C7F':
                # Check for vowel
                if char in VOWELS:
                    roman_word += VOWELS[char]
                # Check for consonant
                elif char in CONSONANTS:
                    base = CONSONANTS[char]
                    # Check for following vowel mark
                    if i + 1 < len(word) and word[i + 1] in VOWEL_MARKS:
                        mark = VOWEL_MARKS[word[i + 1]]
                        if mark:  # Not virama
                            roman_word += base[:-1] + mark  # Replace 'a' with vowel mark
                        else:  # Virama - no vowel
                            roman_word += base[:-1]
                        i += 1
                    else:
                        roman_word += base
                # Check for other marks
                elif char in VOWEL_MARKS:
                    roman_word += VOWEL_MARKS[char]
                else:
                    roman_word += char  # Keep as-is if unknown
            else:
                roman_word += char  # Non-Telugu character
            
            i += 1
        
        result.append(roman_word)
    
    return ' '.join(result)


def process_transcript_for_roman_telugu(segments: list) -> list:
    """
    Process transcript segments and convert Telugu text to Roman Telugu.
    """
    processed = []
    for segment in segments:
        new_segment = segment.copy()
        if 'text' in new_segment:
            new_segment['text'] = transliterate_telugu_to_roman(new_segment['text'])
        processed.append(new_segment)
    return processed


# For testing
if __name__ == "__main__":
    test_cases = [
        "ఎం చేస్తున్నావ్",
        "నువ్వు ఎక్కడ ఉన్నావ్",
        "ఏమైంది రా",
        "ఈ వీడియో చూసావా",
    ]
    
    for telugu in test_cases:
        roman = transliterate_telugu_to_roman(telugu)
        print(f"{telugu} -> {roman}")
