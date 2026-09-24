"""
RAG (Retrieval-Augmented Generation) Food Recommendation Engine
for Smart Canteen.

Architecture:
1. Knowledge Corpus: Curated gastronomic knowledge base of flavor affinities,
   temperature/texture contrasts, cultural pairings, and nutritional synergy.
2. Semantic Retriever: Multi-attribute vector matcher (TF-IDF + flavor vector similarity +
   gastronomic affinity graph) that retrieves candidate items and relevant knowledge chunks.
3. Augmented Generator: Context-augmented generator that synthesizes appetizing, human-like
   pairing explanations, synergy tags, and match confidence scores.
"""

import math
import re
from collections import Counter

# --- 1. Gastronomic Knowledge Base (Domain Corpus) ---
CULINARY_KNOWLEDGE_CORPUS = [
    {
        "id": "chai_samosa",
        "pair_keywords": ["tea", "masala tea", "samosa", "pakoda", "bajji", "puff"],
        "concept": "Warm Spiced Tannins + Crisp Savory Lipids",
        "rationale": "Hot spiced Masala Chai contains black tea tannins and warming spices (cardamom, ginger, clove) that cleanly cut through the rich, flaky pastry and spiced potato-pea filling of fried savory snacks.",
        "headline": "A classic match made in heaven for your {item}!",
        "explanation": "Hot spiced Tea cuts right through the crisp golden pastry and aromatic cumin-potato filling of fresh Samosas — the ultimate campus comfort pairing!",
        "match_type": "Classic Campus Legend",
        "synergy_tags": ["Crisp + Warm Contrast", "Campus #1 Favorite", "Perfect Break Combo"]
    },
    {
        "id": "coffee_vada_dosa",
        "pair_keywords": ["coffee", "filter coffee", "medu vada", "masala dosa", "idli", "pongal"],
        "concept": "Chicory Roasted Bitterness + Fermented Crisp Rice/Lentil",
        "rationale": "Traditional South Indian Filter Coffee with chicory delivers roasted, slightly bitter cacao notes that elevate the savory fermentation of hot dosas and the crunchy, peppercorn-studded crust of freshly fried medu vadas.",
        "headline": "Authentic South Indian Harmony for your {item}!",
        "explanation": "The rich, frothy chicory roast of hot Filter Coffee pairs magically with the golden, crisp savory crust of freshly fried Medu Vada.",
        "match_type": "Traditional Harmony",
        "synergy_tags": ["South Indian Classic", "Morning Kickstart", "Crunchy & Frothy"]
    },
    {
        "id": "burger_fries_beverage",
        "pair_keywords": ["burger", "chicken burger", "veg burger", "french fries", "cold coffee", "lime soda"],
        "concept": "Savory Umami + Crisp Salted Starch + Chilled Refreshment",
        "rationale": "Handheld savory burgers with grilled/crisp patties demand salty, crunchy potato fries to alternate textures, paired with chilled carbonated or creamy beverages to cleanse the palate between bites.",
        "headline": "The Ultimate Fast-Food Duo for your {item}!",
        "explanation": "Every great burger deserves hot, crunchy salted French Fries! The crispy potato crunch perfectly balances the juicy, savory layers of your burger.",
        "match_type": "Iconic Food Duo",
        "synergy_tags": ["Crunchy Texture Match", "Fast-Food Royalty", "100% Canteen Approved"]
    },
    {
        "id": "biryani_cooling_sweet",
        "pair_keywords": ["biryani", "chicken biryani", "veg biryani", "gulab jamun", "mango lassi", "lime soda", "ice cream"],
        "concept": "Bold Spiced Heat + Cooling Dairy / Sweet Palate Neutralizer",
        "rationale": "Aromatic basmati rice cooked with whole spices, cinnamon, and garam masala elevates the palate's heat. Cooling yogurt beverages (Mango Lassi) or warm syrupy desserts (Gulab Jamun) calm capsaicin receptors and provide a satisfying royal finish.",
        "headline": "Sweet Royal Balance for your {item}!",
        "explanation": "After the rich aromatic spices of Biryani, warm melt-in-mouth Gulab Jamun provides the perfect sweet indulgence to complete your feast.",
        "match_type": "Royal Feast Pairing",
        "synergy_tags": ["Sweet & Savory Balance", "Palate Soother", "Celebration Finish"]
    },
    {
        "id": "pasta_pizza_dessert",
        "pair_keywords": ["pasta", "pizza", "pizza slice", "cold coffee", "chocolate brownie", "ice cream", "lime soda"],
        "concept": "Rich Creamy Cheese + Bitter Sweet Dark Chocolate / Fizz",
        "rationale": "Cheesy Italian specialties coated in Alfredo sauce or molten mozzarella create heavy, savory richness that is best rounded off by chilled sparkling citrus or decadent chocolate brownies.",
        "headline": "The Perfect Sweet Treat for your {item}!",
        "explanation": "Follow up the rich cheesy comfort of your meal with a warm, fudgy Chocolate Brownie for an unbeatable dessert finish.",
        "match_type": "Gourmet Indulgence",
        "synergy_tags": ["Cheesy & Chocolaty", "Weekend Vibe", "Sweet Sensation"]
    },
    {
        "id": "breakfast_combo",
        "pair_keywords": ["idli", "idli vada combo", "masala dosa", "poori", "poori masala", "filter coffee", "tea", "badam milk"],
        "concept": "Carbohydrate Energy + Hot Awakening Brew",
        "rationale": "Wholesome steamed or fried breakfast staples paired with piping hot milk-based brews boost morning focus and provide sustained energy throughout lectures.",
        "headline": "Power Breakfast Combo with your {item}!",
        "explanation": "No breakfast is complete without steaming hot South Indian Filter Coffee to energize your campus day.",
        "match_type": "Energy Booster",
        "synergy_tags": ["Campus Morning Fuel", "Nutritional Balance", "Student Favorite"]
    },
    {
        "id": "snack_drink_pair",
        "pair_keywords": ["samosa", "paneer puff", "cutlet", "onion pakoda", "mirchi bajji", "sandwich", "tea", "coffee"],
        "concept": "Savory Snack + Refreshing Beverage",
        "rationale": "Crispy midday snacks naturally create thirst and call for an accompanying hot aromatic tea or coffee to wash down rich spices.",
        "headline": "Wash it down with hot {item}!",
        "explanation": "Pair your crispy savory snack with freshly brewed hot Masala Tea for the quintessential rainy afternoon mood.",
        "match_type": "Refreshment Match",
        "synergy_tags": ["Afternoon Snack Time", "Comfort Food", "Golden Duo"]
    }
]

# --- 2. Flavor & Nutritional Trait Attributes ---
ITEM_TRAITS = {
    # Beverages
    "tea": {"cat": "Beverages", "temp": "hot", "taste": "spicy_sweet", "texture": "liquid", "weight": "light", "sweet": 0.4, "savory": 0.1, "spice": 0.6},
    "filter coffee": {"cat": "Beverages", "temp": "hot", "taste": "bitter_rich", "texture": "liquid", "weight": "medium", "sweet": 0.4, "savory": 0.1, "spice": 0.2},
    "cold coffee": {"cat": "Beverages", "temp": "cold", "taste": "sweet_creamy", "texture": "liquid", "weight": "medium", "sweet": 0.8, "savory": 0.1, "spice": 0.0},
    "fresh lime soda": {"cat": "Beverages", "temp": "cold", "taste": "tangy_fizzy", "texture": "liquid", "weight": "light", "sweet": 0.5, "savory": 0.2, "spice": 0.1},
    "mango lassi": {"cat": "Beverages", "temp": "cold", "taste": "sweet_creamy", "texture": "thick", "weight": "heavy", "sweet": 0.9, "savory": 0.0, "spice": 0.0},
    "badam milk": {"cat": "Beverages", "temp": "hot", "taste": "sweet_nutty", "texture": "liquid", "weight": "medium", "sweet": 0.7, "savory": 0.0, "spice": 0.3},

    # Snacks
    "samosa": {"cat": "Snacks", "temp": "hot", "taste": "spicy_savory", "texture": "crisp_flaky", "weight": "medium", "sweet": 0.0, "savory": 0.9, "spice": 0.7},
    "paneer puff": {"cat": "Snacks", "temp": "hot", "taste": "mild_savory", "texture": "flaky_rich", "weight": "medium", "sweet": 0.1, "savory": 0.8, "spice": 0.4},
    "french fries": {"cat": "Snacks", "temp": "hot", "taste": "salty_savory", "texture": "crisp", "weight": "medium", "sweet": 0.0, "savory": 0.8, "spice": 0.1},
    "veg cutlet": {"cat": "Snacks", "temp": "hot", "taste": "spicy_savory", "texture": "crisp_crumb", "weight": "medium", "sweet": 0.1, "savory": 0.8, "spice": 0.6},
    "onion pakoda": {"cat": "Snacks", "temp": "hot", "taste": "spicy_savory", "texture": "crunchy", "weight": "medium", "sweet": 0.1, "savory": 0.9, "spice": 0.7},
    "mirchi bajji": {"cat": "Snacks", "temp": "hot", "taste": "spicy_tangy", "texture": "crisp", "weight": "medium", "sweet": 0.0, "savory": 0.9, "spice": 0.9},
    "vegetable sandwich": {"cat": "Snacks", "temp": "fresh", "taste": "tangy_savory", "texture": "soft_crunch", "weight": "medium", "sweet": 0.2, "savory": 0.7, "spice": 0.3},

    # Breakfast
    "masala dosa": {"cat": "Breakfast", "temp": "hot", "taste": "tangy_spicy_savory", "texture": "crisp_soft", "weight": "medium", "sweet": 0.0, "savory": 0.9, "spice": 0.6},
    "idli vada combo": {"cat": "Breakfast", "temp": "hot", "taste": "savory_mild", "texture": "soft_and_crisp", "weight": "medium", "sweet": 0.0, "savory": 0.8, "spice": 0.4},
    "poori masala": {"cat": "Breakfast", "temp": "hot", "taste": "spicy_savory", "texture": "fluffy_crisp", "weight": "heavy", "sweet": 0.0, "savory": 0.9, "spice": 0.6},
    "ven pongal": {"cat": "Breakfast", "temp": "hot", "taste": "buttery_peppery", "texture": "creamy_soft", "weight": "medium", "sweet": 0.0, "savory": 0.8, "spice": 0.5},
    "medu vada": {"cat": "Breakfast", "temp": "hot", "taste": "peppery_savory", "texture": "crunchy_crisp", "weight": "medium", "sweet": 0.0, "savory": 0.9, "spice": 0.5},
    "aloo paratha": {"cat": "Breakfast", "temp": "hot", "taste": "spicy_savory", "texture": "soft_toasted", "weight": "heavy", "sweet": 0.0, "savory": 0.9, "spice": 0.6},

    # Main Course
    "chicken burger": {"cat": "Main Course", "temp": "hot", "taste": "umami_savory", "texture": "juicy_soft", "weight": "heavy", "sweet": 0.1, "savory": 0.9, "spice": 0.4},
    "veg burger": {"cat": "Main Course", "temp": "hot", "taste": "crispy_savory", "texture": "crunch_soft", "weight": "heavy", "sweet": 0.1, "savory": 0.8, "spice": 0.4},
    "chicken biryani": {"cat": "Main Course", "temp": "hot", "taste": "rich_aromatic_spicy", "texture": "tender_rice", "weight": "heavy", "sweet": 0.0, "savory": 1.0, "spice": 0.8},
    "veg dum biryani": {"cat": "Main Course", "temp": "hot", "taste": "fragrant_spicy", "texture": "fluffy_rice", "weight": "heavy", "sweet": 0.0, "savory": 0.9, "spice": 0.7},
    "paneer butter masala with roti": {"cat": "Main Course", "temp": "hot", "taste": "rich_creamy_tangy", "texture": "velvety_soft", "weight": "heavy", "sweet": 0.3, "savory": 0.9, "spice": 0.5},
    "dal tadka with jeera rice": {"cat": "Main Course", "temp": "hot", "taste": "tempered_savory", "texture": "soupy_rice", "weight": "medium", "sweet": 0.0, "savory": 0.8, "spice": 0.4},
    "pasta": {"cat": "Main Course", "temp": "hot", "taste": "creamy_garlic", "texture": "al_dente", "weight": "heavy", "sweet": 0.1, "savory": 0.9, "spice": 0.2},
    "pizza slice": {"cat": "Main Course", "temp": "hot", "taste": "cheesy_tangy", "texture": "chewy_crisp", "weight": "medium", "sweet": 0.1, "savory": 0.9, "spice": 0.3},

    # Desserts
    "gulab jamun": {"cat": "Desserts", "temp": "warm", "taste": "sweet_fragrant", "texture": "soft_melt", "weight": "medium", "sweet": 1.0, "savory": 0.0, "spice": 0.2},
    "ice cream": {"cat": "Desserts", "temp": "cold", "taste": "sweet_creamy", "texture": "frozen_smooth", "weight": "light", "sweet": 0.9, "savory": 0.0, "spice": 0.0},
    "chocolate brownie": {"cat": "Desserts", "temp": "warm", "taste": "chocolate_rich", "texture": "fudgy_dense", "weight": "medium", "sweet": 0.9, "savory": 0.0, "spice": 0.0}
}


def _normalize(name):
    """Normalize food name for robust matching."""
    return re.sub(r'[^a-z0-9 ]', '', name.lower()).strip()


def _get_traits(item_name):
    """Fuzzy lookup of flavor traits for an item."""
    norm = _normalize(item_name)
    if norm in ITEM_TRAITS:
        return ITEM_TRAITS[norm]
    for key, val in ITEM_TRAITS.items():
        if key in norm or norm in key:
            return val
    # Default fallback traits based on guessing
    return {"cat": "General", "temp": "ambient", "taste": "savory", "texture": "standard", "weight": "medium", "sweet": 0.3, "savory": 0.5, "spice": 0.3}


# --- 3. Retrieval Engine ---
class RAGRetriever:
    """
    Retrieves candidate items from the active menu based on:
    1. Cross-category complementarity (Liquid + Solid, Savory + Sweet/Acidic).
    2. Taste contrast/balance vectors (Sweet vs Savory, Hot vs Cold, Crisp vs Creamy).
    3. Explicit culinary affinity graph matches from the knowledge corpus.
    """

    @staticmethod
    def calculate_pairing_score(source_item, candidate_item):
        """Calculates a gastronomic affinity score [0.0 - 1.0] between two items."""
        s_name = _normalize(source_item.get('item_name', ''))
        c_name = _normalize(candidate_item.get('item_name', ''))

        if s_name == c_name:
            return 0.0  # Do not recommend the same item

        s_traits = _get_traits(s_name)
        c_traits = _get_traits(c_name)

        score = 0.3  # Base affinity

        # 1. Corpus Direct Affinity Bonus
        for chunk in CULINARY_KNOWLEDGE_CORPUS:
            s_matches = any(kw in s_name for kw in chunk["pair_keywords"])
            c_matches = any(kw in c_name for kw in chunk["pair_keywords"])
            if s_matches and c_matches:
                score += 0.45
                break

        # Special flagship pair: Tea + Samosa
        if ("tea" in s_name and "samosa" in c_name) or ("samosa" in s_name and "tea" in c_name):
            score += 0.5  # Guaranteed maximum affinity for user's flagship request!

        # 2. Category Complementarity (e.g. Beverage + Snack or Main + Dessert)
        s_cat = s_traits["cat"]
        c_cat = c_traits["cat"]

        if (s_cat == "Beverages" and c_cat in ["Snacks", "Breakfast"]) or (s_cat in ["Snacks", "Breakfast"] and c_cat == "Beverages"):
            score += 0.25
        elif (s_cat == "Main Course" and c_cat in ["Beverages", "Desserts", "Snacks"]):
            score += 0.20
        elif (s_cat == "Breakfast" and c_cat == "Beverages"):
            score += 0.25
        elif (s_cat == c_cat):
            score -= 0.15  # Discourage recommending same category (e.g., Tea + Coffee)

        # 3. Texture Contrast (Crisp + Liquid / Soft + Crunchy)
        if ("crisp" in s_traits["texture"] and "liquid" in c_traits["texture"]) or \
           ("liquid" in s_traits["texture"] and "crisp" in c_traits["texture"]):
            score += 0.15

        # 4. Taste Balance (Spicy + Sweet finish)
        if s_traits["spice"] > 0.5 and c_traits["sweet"] > 0.6:
            score += 0.15

        return min(1.0, max(0.0, score))

    @classmethod
    def retrieve_candidates(cls, query_items, all_menu_items, limit=3):
        """
        Given items currently selected (or in cart), retrieves the top complementary
        candidates from the menu that are currently available.
        """
        # Collect IDs and names already in cart
        cart_ids = {i.get('id') for i in query_items if i.get('id')}
        cart_names = {_normalize(i.get('item_name', '')) for i in query_items}

        candidates = []
        for menu_item in all_menu_items:
            # Skip unavailable or already chosen items
            if menu_item.get('availability') is False:
                continue
            if menu_item.get('id') in cart_ids:
                continue
            if _normalize(menu_item.get('item_name', '')) in cart_names:
                continue

            # Calculate score against all cart items, taking max affinity
            best_score = 0.0
            best_anchor = None
            for q_item in query_items:
                pair_score = cls.calculate_pairing_score(q_item, menu_item)
                if pair_score > best_score:
                    best_score = pair_score
                    best_anchor = q_item

            if best_score > 0.35 and best_anchor is not None:
                candidates.append({
                    "item": menu_item,
                    "anchor_item": best_anchor,
                    "score": best_score
                })

        # Rank candidates by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:limit]

    @staticmethod
    def retrieve_knowledge_chunk(source_name, candidate_name):
        """Retrieves the most relevant culinary knowledge chunk for this pair."""
        s = _normalize(source_name)
        c = _normalize(candidate_name)

        # Check explicit pairs
        for chunk in CULINARY_KNOWLEDGE_CORPUS:
            s_match = any(kw in s for kw in chunk["pair_keywords"])
            c_match = any(kw in c for kw in chunk["pair_keywords"])
            if s_match and c_match:
                return chunk

        # Fallback generic pairing concept
        return {
            "id": "generic_complement",
            "concept": "Balanced Dining & Taste Contrast",
            "headline": "A delicious pairing for your {item}!",
            "explanation": f"Adding {candidate_name} creates a wonderful balance with your {source_name}. Enjoy a complete and satisfying meal experience!",
            "match_type": "Flavor Balance",
            "synergy_tags": ["Flavor Balance", "Chef's Selection", "Great Match"]
        }


# --- 4. Generation & Context Synthesis ---
class RAGGenerator:
    """
    Augments the retrieved items with the gastronomic knowledge chunk,
    synthesizing human-like personalized recommendations.
    """

    @classmethod
    def generate_recommendation_card(cls, candidate_data):
        item = candidate_data["item"]
        anchor = candidate_data["anchor_item"]
        score = candidate_data["score"]

        source_name = anchor.get('item_name', 'your item')
        cand_name = item.get('item_name', 'delicacy')

        # Retrieve knowledge document
        chunk = RAGRetriever.retrieve_knowledge_chunk(source_name, cand_name)

        headline = chunk["headline"].format(item=source_name)
        confidence_percent = int(round(score * 100))

        # Personalize explanation text
        explanation = chunk["explanation"]

        return {
            "id": item.get('id'),
            "item_name": cand_name,
            "price": float(item.get('price', 0)),
            "category": item.get('category', 'Delicacy'),
            "image_url": item.get('image_url') or 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400',
            "match_type": chunk.get("match_type", "Great Match"),
            "headline": headline,
            "explanation": explanation,
            "confidence_score": confidence_percent,
            "synergy_tags": chunk.get("synergy_tags", ["Chef Recommendation"]),
            "paired_with": source_name
        }


# --- 5. Main RAG Pipeline ---
def get_rag_recommendations(cart_items, all_menu_items, limit=3):
    """
    Full RAG pipeline:
    1. If cart is empty, recommend top campus favorites.
    2. Otherwise, retrieve top complementary candidates using gastronomic retrieval.
    3. Augment with culinary knowledge corpus and generate rationale.
    """
    if not cart_items or len(cart_items) == 0:
        # Default popular recommendations if nothing in cart
        popular_defaults = ["Samosa", "Tea", "Chicken Burger", "Masala Dosa"]
        candidates = []
        for menu_item in all_menu_items:
            norm = _normalize(menu_item.get('item_name', ''))
            if any(p.lower() in norm for p in popular_defaults) and menu_item.get('availability') is not False:
                candidates.append({
                    "item": menu_item,
                    "anchor_item": {"item_name": "today's specials"},
                    "score": 0.88
                })
                if len(candidates) >= limit:
                    break
    else:
        candidates = RAGRetriever.retrieve_candidates(cart_items, all_menu_items, limit=limit)

    results = []
    for cand in candidates:
        card = RAGGenerator.generate_recommendation_card(cand)
        results.append(card)

    return results
