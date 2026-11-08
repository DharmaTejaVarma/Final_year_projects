from typing import Any, Dict, List
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Knowledge base document with source metadata."""

    title: str
    destination: str
    category: str = Field(..., description="'history', 'culture', 'description', 'travel_tips', or 'attraction'")
    source: str
    content: str


# Alias for explicit typing
KnowledgeDocument = Document


# Curated knowledge base for TravelSenseAI RAG system
CURATED_KNOWLEDGE_BASE: List[Dict[str, str]] = [
    # --- HYDERABAD HISTORICAL & ATTRACTION DATA ---
    {
        "title": "Golconda Fort History and Architecture",
        "destination": "Hyderabad",
        "category": "history",
        "source": "Archaeological Survey of India (ASI) Hyderabad Circle",
        "content": (
            "Golconda Fort was originally built as a mud fort by the Kakatiya dynasty in the 13th century. "
            "It later became the fortified capital of the Qutb Shahi kings (1518–1687) who expanded it into a massive granite citadel. "
            "The fort is renowned for its ingenious acoustic engineering: a hand clap at the Fateh Darwaza entry portico can be heard "
            "clearly at the Bala Hissar pavilion atop the 120-meter high hill, serving as an ancient early warning system. "
            "The fortress also housed the vault where legendary gems including the Koh-i-Noor, Hope Diamond, and Daria-i-Noor were stored. "
            "Visitors should plan for at least 2 to 3 hours to climb the 360 stone stairs and explore the royal apartments, armory, and mosques."
        ),
    },
    {
        "title": "Charminar and the Four Arches",
        "destination": "Hyderabad",
        "category": "history",
        "source": "Telangana State Tourism Archives",
        "content": (
            "Constructed in 1591 CE by Sultan Muhammad Quli Qutb Shah, the fifth ruler of the Qutb Shahi dynasty, "
            "Charminar was built to commemorate the eradication of a devastating plague and mark the founding of the new city of Hyderabad. "
            "The square granite structure features four grand arches facing cardinal directions and four slender 48.7-meter minarets with double balconies. "
            "On the top floor sits an ancient mosque, making Charminar both an Islamic architectural masterpiece and the cultural heartbeat of the city. "
            "Surrounding Charminar is the vibrant Laad Bazaar, world-famous for handcrafted lacquer and glass bangles, traditional zardozi embroidery, and natural pearls."
        ),
    },
    {
        "title": "Qutb Shahi Tombs Heritage Precinct",
        "destination": "Hyderabad",
        "category": "attraction",
        "source": "Aga Khan Trust for Culture (AKTC) Restoration Notes",
        "content": (
            "Located approximately one kilometer north of Golconda Fort's Banjara Darwaza, the Qutb Shahi Tombs form a magnificent necropolis "
            "dedicated to the seven rulers of the Qutb Shahi dynasty. Built in the 16th and 17th centuries, the tombs represent a unique blend "
            "of Persian, Pathan, and Hindu architectural traditions, characterized by bulbous domes, intricate plaster stucco work, and tiered terraces. "
            "The mausoleum of Muhammad Quli Qutb Shah is the grandest of all, standing over 42 meters high. The surrounding Ibrahim Bagh gardens "
            "have been comprehensively restored by the Aga Khan Trust for Culture, making it a peaceful, unhurried cultural walk."
        ),
    },
    {
        "title": "Chowmahalla Palace & Asaf Jahi Dynasty",
        "destination": "Hyderabad",
        "category": "history",
        "source": "Nizam's Trust Heritage Documentation",
        "content": (
            "Chowmahalla Palace ('Four Palaces') was the official seat of the Asaf Jahi dynasty, known as the Nizams of Hyderabad. "
            "Initiated by Nizam Salabat Jung in 1750 and completed by Nizam Afzal-ud-Daula in the 1860s, the palace synthesizes Mughal, Persian, "
            "and European neoclassical architecture. The Khilwat Mubarak (Grand Durbar Hall) boasts nineteen monumental Belgian crystal chandeliers "
            "and the revered Takht-e-Nishan (royal marble throne). The palace grounds also house a museum of vintage royal cars, including a 1912 "
            "canary-yellow Rolls-Royce Silver Ghost, and an armory displaying ceremonial swords and armor."
        ),
    },
    {
        "title": "Salar Jung Museum Artifacts and Collections",
        "destination": "Hyderabad",
        "category": "attraction",
        "source": "Salar Jung Museum National Board Guide",
        "content": (
            "The Salar Jung Museum is one of India's three National Museums and features the world's largest one-man antique collection, "
            "amassed predominantly by Nawab Mir Yousuf Ali Khan (Salar Jung III), Prime Minister to the seventh Nizam. "
            "The museum holds over 46,000 artifacts across 38 galleries. Premier highlights include the 'Veiled Rebecca' carved from translucent "
            "Italian marble by Giovanni Maria Benzoni in 1876, the double-sided wood sculpture of Mephistopheles and Margaretta, the 19th-century "
            "British musical clock that draws crowds every hour, and an extensive collection of jade daggers owned by Mughal Emperors Jahangir and Shah Jahan."
        ),
    },
    # --- HYDERABAD CULTURE & TRAVEL TIPS ---
    {
        "title": "Hyderabadi Culinary Traditions and Food Guide",
        "destination": "Hyderabad",
        "category": "culture",
        "source": "Culinary Heritage Society of Deccan India",
        "content": (
            "Hyderabadi cuisine is a legendary royal synthesis of Mughlai, Turkish, and Arabic culinary influences married with native Telugu spice palettes. "
            "The undisputed crown jewel is Hyderabadi Dum Biryani, cooked using the 'Kacchi' method where marinated mutton and aromatic basmati rice "
            "are sealed with dough and slow-steamed over coals. Key heritage culinary institutions include Paradise Biryani, Bawarchi, and Shadab. "
            "Beyond biryani, visitors must experience Haleem (a slow-cooked stew of wheat, barley, meat, and lentils during Ramadan), "
            "Mirchi ka Salan (tangy chili gravy), Double ka Meetha (saffron bread pudding), and Irani Chai paired with Osmania biscuits at old city tea cafes."
        ),
    },
    {
        "title": "Hyderabad Travel Tips and Navigation Advice",
        "destination": "Hyderabad",
        "category": "travel_tips",
        "source": "TravelSenseAI City Navigation Guidelines",
        "content": (
            "1. Best Season: Visit between October and March when daytime temperatures range comfortably from 20°C to 28°C. "
            "2. Summer Caution: May temperatures routinely exceed 40°C; schedule outdoor fort walks in early morning (09:00 AM) or after 04:00 PM. "
            "3. Transportation: Use the Hyderabad Metro for rapid travel between Secunderabad, Ameerpet, and HITEC City. In Old City areas around "
            "Charminar and Chowmahalla, walking and auto-rickshaws are vastly superior to large cars due to dense pedestrian lanes. "
            "4. Modesty: When visiting Mecca Masjid and active heritage religious shrines, modest clothing covering shoulders and knees is mandatory. "
            "5. Bargaining: Respectful bargaining of 20–30% is customary in street bazaars around Laad Bazaar, but entrance fees to ASI monuments are fixed."
        ),
    },
    # --- BENGALURU HISTORICAL, ATTRACTION & TIPS ---
    {
        "title": "Bengaluru Overview and Garden City Identity",
        "destination": "Bengaluru",
        "category": "description",
        "source": "Karnataka Tourism Development Corporation (KSTDC)",
        "content": (
            "Bengaluru, the capital of Karnataka, sits on the Deccan Plateau at an elevation of 920 meters, bestowing it with pleasant temperate "
            "weather year-round. Originally founded by Kempe Gowda I in 1537 as a mud fort town, it evolved into the 'Garden City of India' "
            "under Hyder Ali and Tipu Sultan, and today stands as the Silicon Valley of India. The city effortlessly balances historic lung spaces "
            "like Lalbagh Botanical Garden and Cubbon Park with grand Victorian government buildings, bustling craft breweries, and tech campuses."
        ),
    },
    {
        "title": "Lalbagh Botanical Garden and Glass House",
        "destination": "Bengaluru",
        "category": "attraction",
        "source": "Directorate of Horticulture Karnataka",
        "content": (
            "Commissioned in 1760 by Hyder Ali and completed by his son Tipu Sultan, Lalbagh Botanical Garden spans 240 acres in southern Bengaluru. "
            "It houses over 1,850 species of rare tropical and subtropical flora, including trees over 100 years old imported from Persia and France. "
            "The centerpiece is the cast-iron Glass House, modeled on London's Crystal Palace in 1889, which hosts the famous biannual flower shows "
            "during Republic Day and Independence Day. Visitors should also view the Lalbagh Rock, a 3,000-million-year-old Peninsular Gneiss formation."
        ),
    },
    {
        "title": "Bangalore Palace and Tipu Sultan Summer Palace",
        "destination": "Bengaluru",
        "category": "history",
        "source": "Mysore Royal Family Archives",
        "content": (
            "Bangalore Palace was built in 1878 by Chamarajendra Wadiyar X in Tudor Revival style with fortified towers, battlements, and ornate wood carvings, "
            "reminiscent of England's Windsor Castle. The interior features elegant floral motifs, stained glass windows, and historic Raja Ravi Varma paintings. "
            "Contrasting this British-influenced royal palace is Tipu Sultan's Summer Palace in Chamrajpet, constructed entirely out of French-carved teakwood "
            "in 1791, known as the 'Abode of Peace' with fluted wooden pillars and Persian floral wall frescoes."
        ),
    },
    {
        "title": "Bengaluru Travel Tips and Craft Beer Scene",
        "destination": "Bengaluru",
        "category": "travel_tips",
        "source": "Karnataka Tourism City Guide",
        "content": (
            "1. Peak Traffic: Bengaluru traffic is notoriously heavy between 08:30–11:00 AM and 05:30–08:30 PM. Group visits by geographic hubs "
            "(e.g., Central Cubbon Park/MG Road on Day 1; South Lalbagh/Jayanagar on Day 2). "
            "2. Namma Metro: Use the Purple and Green Metro lines to easily navigate east-west and north-south axes without traffic delays. "
            "3. Microbreweries: Known as India's pub capital, Indiranagar and Koramangala offer world-class craft breweries such as Toit, Windmills Craftworks, "
            "and Arbor Brewing Company. "
            "4. South Indian Breakfast: Must-visit breakfast institutions include Vidyarthi Bhavan in Gandhi Bazaar for crispy masala dosa and filter coffee."
        ),
    },
]


def load_curated_documents() -> List[Document]:
    """Load curated destination knowledge documents."""
    return [Document(**doc) for doc in CURATED_KNOWLEDGE_BASE]
