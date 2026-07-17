# Transliteration Method Samples

Randomly sampled records (seed=42) comparing all implemented methods against the original Sinhala Unicode source. 25 from SinhalaMMLU, 25 from SOLD (50 total).

Method key: **Phonetic** = in-house deterministic baseline (`phonetic.py`) · **Aksharamukha** = external library (`aksharamukha_method.py`) · **G2P phonemic** = Wasala et al. 2006 rule-based G2P, retains IPA schwa `ə` (`sinhala_g2p.py`, `transliterate`) · **G2P ASCII** = same rule engine with `ə→a` projected for keyboard-typable output (`sinhala_g2p.py`, `transliterate_ascii`) · **uroman** = external universal romanizer (`uroman_method.py`)

---

## SinhalaMMLU samples

### 1. `mmlu_0052` (Humanities / Easy)

**Sinhala:** බුදුන් වහන්සේගේ පටිධාතුව තැන්පත් කර නිර්මාණය කරන ලද දාගැබ වන්නේ,

- **Phonetic (baseline):** budun wahanseegee patidhaathuwa thaenpath kara nirmaanaya karana lada daagaeba wannee,
- **Aksharamukha:** budun wahanseegee patidhaatuwa taenpat kara nirmaanaya karana lada daagaeba wannee,
- **Sinhala G2P (phonemic, retains ə):** budun wahanseegee patidaatuwə taenpat kərə nirmaanəyə kərənə ladə daagaebə wannee,
- **Sinhala G2P (ASCII, ə→a):** budun wahanseegee patidaatuwa taenpat kara nirmaanaya karana lada daagaeba wannee,
- **uroman:** budun vahanseegee pattidaatuva taenpat kara nirmaanaya karana lada daagaeba vannee,

**Options (Sinhala → romanized per method):**

- අභයගිරිය දාගැබ
  - Phonetic (baseline): abhayagiriya daagaeba
  - Aksharamukha: abhayagiriya daagaeba
  - Sinhala G2P (phonemic, retains ə): abəyəgiriyə daagaebə
  - Sinhala G2P (ASCII, ə→a): abayagiriya daagaeba
  - uroman: abayagiriya daagaeba
- රන්කොත් වෙහෙර
  - Phonetic (baseline): rankoth wehera
  - Aksharamukha: rankot wehera
  - Sinhala G2P (phonemic, retains ə): rankot weherə
  - Sinhala G2P (ASCII, ə→a): rankot wehera
  - uroman: rankot vehera
- ථුපාරාමය දාගැබ
  - Phonetic (baseline): thupaaraamaya daagaeba
  - Aksharamukha: thupaaraamaya daagaeba
  - Sinhala G2P (phonemic, retains ə): tupaaraaməyə daagaebə
  - Sinhala G2P (ASCII, ə→a): tupaaraamaya daagaeba
  - uroman: tupaaraamaya daagaeba
- ජේතවනාරාම දාගැබ ✅
  - Phonetic (baseline): jeethawanaaraama daagaeba
  - Aksharamukha: jeetawanaaraama daagaeba
  - Sinhala G2P (phonemic, retains ə): jeetəwənaaraamə daagaebə
  - Sinhala G2P (ASCII, ə→a): jeetawanaaraama daagaeba
  - uroman: jeetavanaaraama daagaeba

---

### 2. `mmlu_0055` (Humanities / Easy)

**Sinhala:** චීත්ත රෙද්දක් නිර්මාණය සඳහා වඩාත් සුදුසු මෝස්තර වර්ගය වන්නේ

- **Phonetic (baseline):** chiiththa reddak nirmaanaya sandahaa wadaath sudusu moosthara wargaya wannee
- **Aksharamukha:** chiitta reddak nirmaanaya sandahaa wadaat sudusu moostara wargaya wannee
- **Sinhala G2P (phonemic, retains ə):** chiittə reddak nirmaanəyə sandəhaa wadaat sudusu moostərə wargəyə wannee
- **Sinhala G2P (ASCII, ə→a):** chiitta reddak nirmaanaya sandahaa wadaat sudusu moostara wargaya wannee
- **uroman:** ciitta reddak nirmaanaya sadahaa vaddaat sudusu moostara vargaya vannee

**Options (Sinhala → romanized per method):**

- වෘත්තාකාර මෝස්තර
  - Phonetic (baseline): wruththaakaara moosthara
  - Aksharamukha: wruttaakaara moostara
  - Sinhala G2P (phonemic, retains ə): wruttaakaarə moostərə
  - Sinhala G2P (ASCII, ə→a): wruttaakaara moostara
  - uroman: vrattaakaara moostara
- මුළුනල මෝස්තර
  - Phonetic (baseline): mulunala moosthara
  - Aksharamukha: mulunala moostara
  - Sinhala G2P (phonemic, retains ə): mulunələ moostərə
  - Sinhala G2P (ASCII, ə→a): mulunala moostara
  - uroman: mulunala moostara
- ව්‍යාප්ත මෝස්තර ✅
  - Phonetic (baseline): wyaaptha moosthara
  - Aksharamukha: wyaapta moostara
  - Sinhala G2P (phonemic, retains ə): wyaaptə moostərə
  - Sinhala G2P (ASCII, ə→a): wyaapta moostara
  - uroman: vyaapta moostara
- වාටි මෝස්තර
  - Phonetic (baseline): waati moosthara
  - Aksharamukha: waati moostara
  - Sinhala G2P (phonemic, retains ə): waati moostərə
  - Sinhala G2P (ASCII, ə→a): waati moostara
  - uroman: vaatti moostara

---

### 3. `mmlu_0062` (Humanities / Easy)

**Sinhala:** ලක්දිව ඉදිකළ පළමු ස්ථූපය ලෙස හඳුන්වන්නේ,

- **Phonetic (baseline):** lakdiwa idikala palamu sthuupaya lesa handunwannee,
- **Aksharamukha:** lakdiwa idikala palamu sthuupaya lesa handunwannee,
- **Sinhala G2P (phonemic, retains ə):** lakdiwə idikələ paləmu stuupəyə lesə handunwannee,
- **Sinhala G2P (ASCII, ə→a):** lakdiwa idikala palamu stuupaya lesa handunwannee,
- **uroman:** lakdiva idikala palamu stuupaya lesa hadunvannee,

**Options (Sinhala → romanized per method):**

- කැලණි විහාරයයි.
  - Phonetic (baseline): kaelani wihaarayayi.
  - Aksharamukha: kaelani wihaarayayi.
  - Sinhala G2P (phonemic, retains ə): kaeləni wihaarəyai.
  - Sinhala G2P (ASCII, ə→a): kaelani wihaarayai.
  - uroman: kaelani vihaarayayi.
- ථූපාරාම විහාරයයි.
  - Phonetic (baseline): thuupaaraama wihaarayayi.
  - Aksharamukha: thuupaaraama wihaarayayi.
  - Sinhala G2P (phonemic, retains ə): tuupaaraamə wihaarəyai.
  - Sinhala G2P (ASCII, ə→a): tuupaaraama wihaarayai.
  - uroman: tuupaaraama vihaarayayi.
- අභයගිරි විහාරයයි. ✅
  - Phonetic (baseline): abhayagiri wihaarayayi.
  - Aksharamukha: abhayagiri wihaarayayi.
  - Sinhala G2P (phonemic, retains ə): abəyəgiri wihaarəyai.
  - Sinhala G2P (ASCII, ə→a): abayagiri wihaarayai.
  - uroman: abayagiri vihaarayayi.
- ජේතවන විහාරයයි.
  - Phonetic (baseline): jeethawana wihaarayayi.
  - Aksharamukha: jeetawana wihaarayayi.
  - Sinhala G2P (phonemic, retains ə): jeetəwənə wihaarəyai.
  - Sinhala G2P (ASCII, ə→a): jeetawana wihaarayai.
  - uroman: jeetavana vihaarayayi.

---

### 4. `mmlu_0066` (Humanities / Easy)

**Sinhala:** නූල් රූකඩ නිර්මාණයේ දී රූකඩ සෑදීම සඳහා ප්‍රධාන වශයෙන් දැව භාවිතා කරන අතර ඒ සඳහා වැඩි වශයෙන් භාවිත කරන දැව වර්ගය නම්

- **Phonetic (baseline):** nuul ruukada nirmaanayee dii ruukada saaediima sandahaa pradhaana washayen daewa bhaawithaa karana athara ee sandahaa waedi washayen bhaawitha karana daewa wargaya nam
- **Aksharamukha:** nuul ruukada nirmaanayee dii ruukada saaediima sandahaa pradhaana washayen daewa bhaawitaa karana atara ee sandahaa waedi washayen bhaawita karana daewa wargaya nam
- **Sinhala G2P (phonemic, retains ə):** nuul ruukədə nirmaanəyee dii ruukədə saaediimə sandəhaa prədaanə washəyen daewə baawitaa kərənə atərə ee sandəhaa waedi washəyen baawitə kərənə daewə wargəyə nam
- **Sinhala G2P (ASCII, ə→a):** nuul ruukada nirmaanayee dii ruukada saaediima sandahaa pradaana washayen daewa baawitaa karana atara ee sandahaa waedi washayen baawita karana daewa wargaya nam
- **uroman:** nuul ruukadda nirmaanayee dii ruukadda saediima sadahaa pradaana vasayen daeva baavitaa karana atara ee sadahaa vaeddi vasayen baavita karana daeva vargaya nam

**Options (Sinhala → romanized per method):**

- කළුවර
  - Phonetic (baseline): kaluwara
  - Aksharamukha: kaluwara
  - Sinhala G2P (phonemic, retains ə): kaluwərə
  - Sinhala G2P (ASCII, ə→a): kaluwara
  - uroman: kaluvara
- තේක්ක
  - Phonetic (baseline): theekka
  - Aksharamukha: teekka
  - Sinhala G2P (phonemic, retains ə): teekkə
  - Sinhala G2P (ASCII, ə→a): teekka
  - uroman: teekka
- රුක්අත්තන ✅
  - Phonetic (baseline): rukaththana
  - Aksharamukha: rukattana
  - Sinhala G2P (phonemic, retains ə): rukattənə
  - Sinhala G2P (ASCII, ə→a): rukattana
  - uroman: rukattana
- බුරුත
  - Phonetic (baseline): burutha
  - Aksharamukha: buruta
  - Sinhala G2P (phonemic, retains ə): burutə
  - Sinhala G2P (ASCII, ə→a): buruta
  - uroman: buruta

---

### 5. `mmlu_0179` (Humanities / Easy)

**Sinhala:** බුදුරජාණන් වහන්සේ කළගුණ දැක්වීම වශයෙන් අනිමිස ලෝචන පූජාව සිදුකරන ලද්දේ කී වන සතියේදී ද ?

- **Phonetic (baseline):** budurajaanan wahansee kalaguna daekwiima washayen animisa loochana puujaawa sidukarana laddee kii wana sathiyeedii da ?
- **Aksharamukha:** budurajaanan wahansee kalaguna daekwiima washayen animisa loochana puujaawa sidukarana laddee kii wana satiyeedii da ?
- **Sinhala G2P (phonemic, retains ə):** budurəjaanan wahansee kaləgunə daekwiimə washəyen animisə loochənə puujaawə sidukərənə laddee kii wanə satiyeedii də ?
- **Sinhala G2P (ASCII, ə→a):** budurajaanan wahansee kalaguna daekwiima washayen animisa loochana puujaawa sidukarana laddee kii wana satiyeedii da ?
- **uroman:** budurajaanan vahansee kalaguna daekviima vasayen animisa loocana puujaava sidukarana laddee kii vana satiyeedii da ?

**Options (Sinhala → romanized per method):**

- පළමුවන සතියේ දී ය.
  - Phonetic (baseline): palamuwana sathiyee dii ya.
  - Aksharamukha: palamuwana satiyee dii ya.
  - Sinhala G2P (phonemic, retains ə): paləmuwənə satiyee dii yə.
  - Sinhala G2P (ASCII, ə→a): palamuwana satiyee dii ya.
  - uroman: palamuvana satiyee dii ya.
- දෙවන සතියේ දී ය. ✅
  - Phonetic (baseline): dewana sathiyee dii ya.
  - Aksharamukha: dewana satiyee dii ya.
  - Sinhala G2P (phonemic, retains ə): dewənə satiyee dii yə.
  - Sinhala G2P (ASCII, ə→a): dewana satiyee dii ya.
  - uroman: devana satiyee dii ya.
- තෙවන සතියේ දී ය .
  - Phonetic (baseline): thewana sathiyee dii ya .
  - Aksharamukha: tewana satiyee dii ya .
  - Sinhala G2P (phonemic, retains ə): tewənə satiyee dii yə .
  - Sinhala G2P (ASCII, ə→a): tewana satiyee dii ya .
  - uroman: tevana satiyee dii ya .
- පස්වන සතියේ දී ය.
  - Phonetic (baseline): paswana sathiyee dii ya.
  - Aksharamukha: paswana satiyee dii ya.
  - Sinhala G2P (phonemic, retains ə): paswənə satiyee dii yə.
  - Sinhala G2P (ASCII, ə→a): paswana satiyee dii ya.
  - uroman: pasvana satiyee dii ya.

---

### 6. `mmlu_0192` (Humanities / Easy)

**Sinhala:** මිනිසා හා සතුන් අතර වෙනස්කම් දක්නට ලැබේ. වෙනස්කම් අතර මිනිසා සතුන්ගෙන් වෙනස් වන්නේ,

- **Phonetic (baseline):** minisaa haa sathun athara wenaskam daknata laebee. wenaskam athara minisaa sathungen wenas wannee,
- **Aksharamukha:** minisaa haa satun atara wenaskam daknata laebee. wenaskam atara minisaa satungen wenas wannee,
- **Sinhala G2P (phonemic, retains ə):** minisaa haa satun atərə wenaskam daknətə laebee. wenaskam atərə minisaa satungen wenas wannee,
- **Sinhala G2P (ASCII, ə→a):** minisaa haa satun atara wenaskam daknata laebee. wenaskam atara minisaa satungen wenas wannee,
- **uroman:** minisaa haa satun atara venaskam daknatta laebee. venaskam atara minisaa satungen venas vannee,

**Options (Sinhala → romanized per method):**

- සදාචාර සම්පන්න බව නිසාය. ✅
  - Phonetic (baseline): sadaachaara sampanna bawa nisaaya.
  - Aksharamukha: sadaachaara sampanna bawa nisaaya.
  - Sinhala G2P (phonemic, retains ə): sadaachaarə sampannə bawə nisaayə.
  - Sinhala G2P (ASCII, ə→a): sadaachaara sampanna bawa nisaaya.
  - uroman: sadaacaara sampanna bava nisaaya.
- සදාචාරයෙන් තොර බව නිසාය.
  - Phonetic (baseline): sadaachaarayen thora bawa nisaaya.
  - Aksharamukha: sadaachaarayen tora bawa nisaaya.
  - Sinhala G2P (phonemic, retains ə): sadaachaarəyen torə bawə nisaayə.
  - Sinhala G2P (ASCII, ə→a): sadaachaarayen tora bawa nisaaya.
  - uroman: sadaacaarayen tora bava nisaaya.
- අධ්‍යාපනයට යොමු නොවීම නිසා ය.
  - Phonetic (baseline): adhyaapanayata yomu nowiima nisaa ya.
  - Aksharamukha: adhyaapanayata yomu nowiima nisaa ya.
  - Sinhala G2P (phonemic, retains ə): adyaapənəyətə yomu nowiimə nisaa yə.
  - Sinhala G2P (ASCII, ə→a): adyaapanayata yomu nowiima nisaa ya.
  - uroman: adyaapanayatta yomu noviima nisaa ya.
- දෙමාපියන්ට නොසැළකීම නිසා ය.
  - Phonetic (baseline): demaapiyanta nosaelakiima nisaa ya.
  - Aksharamukha: demaapiyanta nosaelakiima nisaa ya.
  - Sinhala G2P (phonemic, retains ə): demaapiyantə nosaeləkiimə nisaa yə.
  - Sinhala G2P (ASCII, ə→a): demaapiyanta nosaelakiima nisaa ya.
  - uroman: demaapiyantta nosaelakiima nisaa ya.

---

### 7. `mmlu_0210` (Humanities / Easy)

**Sinhala:** සිගාලෝවාද සූත්‍රයේ ගුරුවරුන් උපමා කර ඇති දිශාව වන්නේ ,

- **Phonetic (baseline):** sigaaloowaada suuthrayee guruwarun upamaa kara aethi dishaawa wannee ,
- **Aksharamukha:** sigaaloowaada suutrayee guruwarun upamaa kara aeti dishaawa wannee ,
- **Sinhala G2P (phonemic, retains ə):** sigaaloowaadə suutrayee guruwərun upəmaa kərə aeti dishaawə wannee ,
- **Sinhala G2P (ASCII, ə→a):** sigaaloowaada suutrayee guruwarun upamaa kara aeti dishaawa wannee ,
- **uroman:** sigaaloovaada suutrayee guruvarun upamaa kara aeti disaava vannee ,

**Options (Sinhala → romanized per method):**

- උතුරු දිසාවය
  - Phonetic (baseline): uthuru disaawaya
  - Aksharamukha: uturu disaawaya
  - Sinhala G2P (phonemic, retains ə): uturu disaawəyə
  - Sinhala G2P (ASCII, ə→a): uturu disaawaya
  - uroman: uturu disaavaya
- බටහිර දිසාවය
  - Phonetic (baseline): batahira disaawaya
  - Aksharamukha: batahira disaawaya
  - Sinhala G2P (phonemic, retains ə): batəhirə disaawəyə
  - Sinhala G2P (ASCII, ə→a): batahira disaawaya
  - uroman: battahira disaavaya
- දකුණු දිසාවය ✅
  - Phonetic (baseline): dakunu disaawaya
  - Aksharamukha: dakunu disaawaya
  - Sinhala G2P (phonemic, retains ə): dakunu disaawəyə
  - Sinhala G2P (ASCII, ə→a): dakunu disaawaya
  - uroman: dakunu disaavaya
- උඩ දිසාවය
  - Phonetic (baseline): uda disaawaya
  - Aksharamukha: uda disaawaya
  - Sinhala G2P (phonemic, retains ə): udə disaawəyə
  - Sinhala G2P (ASCII, ə→a): uda disaawaya
  - uroman: udda disaavaya

---

### 8. `mmlu_0229` (Humanities / Easy)

**Sinhala:** බුදු දහමට අනුව දැහැමි රැකියාවක් නොවන්නේ,

- **Phonetic (baseline):** budu dahamata anuwa daehaemi raekiyaawak nowannee,
- **Aksharamukha:** budu dahamata anuwa daehaemi raekiyaawak nowannee,
- **Sinhala G2P (phonemic, retains ə):** budu dahamətə anuwə daehaemi raekiyaawak nowannee,
- **Sinhala G2P (ASCII, ə→a):** budu dahamata anuwa daehaemi raekiyaawak nowannee,
- **uroman:** budu dahamatta anuva daehaemi raekiyaavak novannee,

**Options (Sinhala → romanized per method):**

- කෘෂිකර්මාන්තය
  - Phonetic (baseline): krushikarmaanthaya
  - Aksharamukha: krushikarmaantaya
  - Sinhala G2P (phonemic, retains ə): krushikarmaantəyə
  - Sinhala G2P (ASCII, ə→a): krushikarmaantaya
  - uroman: krasikarmaantaya
- ගව පාලනය
  - Phonetic (baseline): gawa paalanaya
  - Aksharamukha: gawa paalanaya
  - Sinhala G2P (phonemic, retains ə): gawə paalənəyə
  - Sinhala G2P (ASCII, ə→a): gawa paalanaya
  - uroman: gava paalanaya
- රාජ්‍ය සේවය
  - Phonetic (baseline): raajya seewaya
  - Aksharamukha: raajya seewaya
  - Sinhala G2P (phonemic, retains ə): raajyə seewəyə
  - Sinhala G2P (ASCII, ə→a): raajya seewaya
  - uroman: raajya seevaya
- සත්ත්ව වෙළෙඳාම ✅
  - Phonetic (baseline): saththwa welendaama
  - Aksharamukha: sattwa welendaama
  - Sinhala G2P (phonemic, retains ə): sattwə welendaamə
  - Sinhala G2P (ASCII, ə→a): sattwa welendaama
  - uroman: sattva veledaama

---

### 9. `mmlu_0286` (Humanities / Easy)

**Sinhala:** දේව දරුකම නමැති නොමැකෙන ලාංඡනය පුද්ගල ආත්මය තුළ සනිටුහන් කරන දේව ප්‍රසාද නිධානය වන්නේ ,

- **Phonetic (baseline):** deewa darukama namaethi nomaekena laanchhanaya pudgala aathmaya thula sanituhan karana deewa prasaada nidhaanaya wannee ,
- **Aksharamukha:** deewa darukama namaeti nomaekena laanchhanaya pudgala aatmaya tula sanituhan karana deewa prasaada nidhaanaya wannee ,
- **Sinhala G2P (phonemic, retains ə):** deewə darukəmə namaeti nomaekenə laangchənəyə pudgələ aatməyə tulə sanituhan kərənə deewə prəsaadə nidaanəyə wannee ,
- **Sinhala G2P (ASCII, ə→a):** deewa darukama namaeti nomaekena laangchanaya pudgala aatmaya tula sanituhan karana deewa prasaada nidaanaya wannee ,
- **uroman:** deeva darukama namaeti nomaekena laancanaya pudgala aatmaya tula sanittuhan karana deeva prasaada nidaanaya vannee ,

**Options (Sinhala → romanized per method):**

- ප්‍රසාද ස්නාපනය ය . ✅
  - Phonetic (baseline): prasaada snaapanaya ya .
  - Aksharamukha: prasaada snaapanaya ya .
  - Sinhala G2P (phonemic, retains ə): prəsaadə snaapənəyə yə .
  - Sinhala G2P (ASCII, ə→a): prasaada snaapanaya ya .
  - uroman: prasaada snaapanaya ya .
- පූජකවරය ය .
  - Phonetic (baseline): puujakawaraya ya .
  - Aksharamukha: puujakawaraya ya .
  - Sinhala G2P (phonemic, retains ə): puujəkəwərəyə yə .
  - Sinhala G2P (ASCII, ə→a): puujakawaraya ya .
  - uroman: puujakavaraya ya .
- දිව්‍ය සත්ප්‍රසාදය ය .
  - Phonetic (baseline): diwya sathprasaadaya ya .
  - Aksharamukha: diwya satprasaadaya ya .
  - Sinhala G2P (phonemic, retains ə): diwyə satprasaadəyə yə .
  - Sinhala G2P (ASCII, ə→a): diwya satprasaadaya ya .
  - uroman: divya satprasaadaya ya .
- රෝගීන්ගේ ආලේපය ය .
  - Phonetic (baseline): roogiingee aaleepaya ya .
  - Aksharamukha: roogiingee aaleepaya ya .
  - Sinhala G2P (phonemic, retains ə): roogiingee aaleepəyə yə .
  - Sinhala G2P (ASCII, ə→a): roogiingee aaleepaya ya .
  - uroman: roogiingee aaleepaya ya .

---

### 10. `mmlu_0448` (Humanities / Easy)

**Sinhala:** අපේ එදිනෙදා අවශ්‍යතා ගැන අප ,

- **Phonetic (baseline):** apee edinedaa awashyathaa gaena apa ,
- **Aksharamukha:** apee edinedaa awashyataa gaena apa ,
- **Sinhala G2P (phonemic, retains ə):** apee edinedaa awashyətaa gaenə apə ,
- **Sinhala G2P (ASCII, ə→a):** apee edinedaa awashyataa gaena apa ,
- **uroman:** apee edinedaa avasyataa gaena apa ,

**Options (Sinhala → romanized per method):**

- කරදර විය යුතු ය .
  - Phonetic (baseline): karadara wiya yuthu ya .
  - Aksharamukha: karadara wiya yutu ya .
  - Sinhala G2P (phonemic, retains ə): kərədərə wiyə yutu yə .
  - Sinhala G2P (ASCII, ə→a): karadara wiya yutu ya .
  - uroman: karadara viya yutu ya .
- බලාපොරොත්තු විය යුතු ය .
  - Phonetic (baseline): balaaporoththu wiya yuthu ya .
  - Aksharamukha: balaaporottu wiya yutu ya .
  - Sinhala G2P (phonemic, retains ə): balaaporottu wiyə yutu yə .
  - Sinhala G2P (ASCII, ə→a): balaaporottu wiya yutu ya .
  - uroman: balaaporottu viya yutu ya .
- කනස්සලු විය යුතු ය .
  - Phonetic (baseline): kanassalu wiya yuthu ya .
  - Aksharamukha: kanassalu wiya yutu ya .
  - Sinhala G2P (phonemic, retains ə): kanassəlu wiyə yutu yə .
  - Sinhala G2P (ASCII, ə→a): kanassalu wiya yutu ya .
  - uroman: kanassalu viya yutu ya .
- දෙවිඳුන්ට භාර කළ යුතු ය . ✅
  - Phonetic (baseline): dewindunta bhaara kala yuthu ya .
  - Aksharamukha: dewindunta bhaara kala yutu ya .
  - Sinhala G2P (phonemic, retains ə): dewinduntə baarə kələ yutu yə .
  - Sinhala G2P (ASCII, ə→a): dewindunta baara kala yutu ya .
  - uroman: deviduntta baara kala yutu ya .

---

### 11. `mmlu_0458` (Humanities / Easy)

**Sinhala:** ගලීල මුහුද සඳහා යෙදෙන තවත් නමක් වන්නේ ,

- **Phonetic (baseline):** galiila muhuda sandahaa yedena thawath namak wannee ,
- **Aksharamukha:** galiila muhuda sandahaa yedena tawat namak wannee ,
- **Sinhala G2P (phonemic, retains ə):** galiilə muhudə sandəhaa yedenə tawat namak wannee ,
- **Sinhala G2P (ASCII, ə→a):** galiila muhuda sandahaa yedena tawat namak wannee ,
- **uroman:** galiila muhuda sadahaa yedena tavat namak vannee ,

**Options (Sinhala → romanized per method):**

- රතු මුහුද
  - Phonetic (baseline): rathu muhuda
  - Aksharamukha: ratu muhuda
  - Sinhala G2P (phonemic, retains ə): ratu muhudə
  - Sinhala G2P (ASCII, ə→a): ratu muhuda
  - uroman: ratu muhuda
- මළ මුහුද
  - Phonetic (baseline): mala muhuda
  - Aksharamukha: mala muhuda
  - Sinhala G2P (phonemic, retains ə): malə muhudə
  - Sinhala G2P (ASCII, ə→a): mala muhuda
  - uroman: mala muhuda
- මධ්‍යධරණී මුහුද
  - Phonetic (baseline): madhyadharanii muhuda
  - Aksharamukha: madhyadharanii muhuda
  - Sinhala G2P (phonemic, retains ə): madyədərənii muhudə
  - Sinhala G2P (ASCII, ə→a): madyadaranii muhuda
  - uroman: madyadaranii muhuda
- තිබේරියස් මුහුද ✅
  - Phonetic (baseline): thibeeriyas muhuda
  - Aksharamukha: tibeeriyas muhuda
  - Sinhala G2P (phonemic, retains ə): tibeeriyas muhudə
  - Sinhala G2P (ASCII, ə→a): tibeeriyas muhuda
  - uroman: tibeeriyas muhuda

---

### 12. `mmlu_0477` (Humanities / Easy)

**Sinhala:** උත්ථාන වූ ජේසුස් වහන්සේගේ ඇණ කැළැල් දැක විශ්වාස කළ ගෝලයා වන්නේ ,

- **Phonetic (baseline):** uththaana wuu jeesus wahanseegee aena kaelael daeka wishwaasa kala goolayaa wannee ,
- **Aksharamukha:** utthaana wuu jeesus wahanseegee aena kaelael daeka wishwaasa kala goolayaa wannee ,
- **Sinhala G2P (phonemic, retains ə):** uttaanə wuu jeesus wahanseegee aenə kaelael daekə wishwaasə kələ gooləyaa wannee ,
- **Sinhala G2P (ASCII, ə→a):** uttaana wuu jeesus wahanseegee aena kaelael daeka wishwaasa kala goolayaa wannee ,
- **uroman:** uttaana vuu jeesus vahanseegee aena kaelael daeka visvaasa kala goolayaa vannee ,

**Options (Sinhala → romanized per method):**

- පේදුරුය
  - Phonetic (baseline): peeduruya
  - Aksharamukha: peeduruya
  - Sinhala G2P (phonemic, retains ə): peeduruyə
  - Sinhala G2P (ASCII, ə→a): peeduruya
  - uroman: peeduruya
- තෝමස් ය .
  - Phonetic (baseline): thoomas ya .
  - Aksharamukha: toomas ya .
  - Sinhala G2P (phonemic, retains ə): toomas yə .
  - Sinhala G2P (ASCII, ə→a): toomas ya .
  - uroman: toomas ya .
- ජොහාන් ය . ✅
  - Phonetic (baseline): johaan ya .
  - Aksharamukha: johaan ya .
  - Sinhala G2P (phonemic, retains ə): johaan yə .
  - Sinhala G2P (ASCII, ə→a): johaan ya .
  - uroman: johaan ya .
- මත්තියස් ය .
  - Phonetic (baseline): maththiyas ya .
  - Aksharamukha: mattiyas ya .
  - Sinhala G2P (phonemic, retains ə): mattiyas yə .
  - Sinhala G2P (ASCII, ə→a): mattiyas ya .
  - uroman: mattiyas ya .

---

### 13. `mmlu_0502` (Humanities / Easy)

**Sinhala:** පංච පුස්තකයෙහි සඳහන් කර්තෘ සහ උප කර්තෘ වන්නේ ,

- **Phonetic (baseline):** pancha pusthakayehi sandahan karthru saha upa karthru wannee ,
- **Aksharamukha:** pancha pustakayehi sandahan kartru saha upa kartru wannee ,
- **Sinhala G2P (phonemic, retains ə):** pangchə pustəkəyehi sandəhan kartru saha upə kartru wannee ,
- **Sinhala G2P (ASCII, ə→a):** pangcha pustakayehi sandahan kartru saha upa kartru wannee ,
- **uroman:** panca pustakayehi sadahan kartra saha upa kartra vannee ,

**Options (Sinhala → romanized per method):**

- දෙවියන් වහන්සේ සහ යේසුස් වහන්සේ .
  - Phonetic (baseline): dewiyan wahansee saha yeesus wahansee .
  - Aksharamukha: dewiyan wahansee saha yeesus wahansee .
  - Sinhala G2P (phonemic, retains ə): dewiyan wahansee saha yeesus wahansee .
  - Sinhala G2P (ASCII, ə→a): dewiyan wahansee saha yeesus wahansee .
  - uroman: deviyan vahansee saha yeesus vahansee .
- දෙවියන් වහන්සේ සහ මිනිසා . ✅
  - Phonetic (baseline): dewiyan wahansee saha minisaa .
  - Aksharamukha: dewiyan wahansee saha minisaa .
  - Sinhala G2P (phonemic, retains ə): dewiyan wahansee saha minisaa .
  - Sinhala G2P (ASCII, ə→a): dewiyan wahansee saha minisaa .
  - uroman: deviyan vahansee saha minisaa .
- යේසුස් වහන්සේ සහ මිනිසා .
  - Phonetic (baseline): yeesus wahansee saha minisaa .
  - Aksharamukha: yeesus wahansee saha minisaa .
  - Sinhala G2P (phonemic, retains ə): yeesus wahansee saha minisaa .
  - Sinhala G2P (ASCII, ə→a): yeesus wahansee saha minisaa .
  - uroman: yeesus vahansee saha minisaa .
- දෙවියන් වහන්සේ සහ ආබ්‍රහම් ය .
  - Phonetic (baseline): dewiyan wahansee saha aabraham ya .
  - Aksharamukha: dewiyan wahansee saha aabraham ya .
  - Sinhala G2P (phonemic, retains ə): dewiyan wahansee saha aabraham yə .
  - Sinhala G2P (ASCII, ə→a): dewiyan wahansee saha aabraham ya .
  - uroman: deviyan vahansee saha aabraham ya .

---

### 14. `mmlu_0564` (Social_Science / Easy)

**Sinhala:** විවේකය ඇතිවිට ඔබ ක්‍රීඩා කටයුතුවල යෙදීමෙන් ඔබ තුළ වර්ධනය වන ගුණාංගයක් වන්නේ,

- **Phonetic (baseline):** wiweekaya aethiwita oba kriidaa katayuthuwala yediimen oba thula wardhanaya wana gunaangayak wannee,
- **Aksharamukha:** wiweekaya aetiwita oba kriidaa katayutuwala yediimen oba tula wardhanaya wana gunaangayak wannee,
- **Sinhala G2P (phonemic, retains ə):** wiweekəyə aetiwitə obə kriidaa katəyutuwələ yediimen obə tulə wardənəyə wanə gunaanggəyak wannee,
- **Sinhala G2P (ASCII, ə→a):** wiweekaya aetiwita oba kriidaa katayutuwala yediimen oba tula wardanaya wana gunaanggayak wannee,
- **uroman:** viveekaya aetivitta oba kriiddaa kattayutuvala yediimen oba tula vardanaya vana gunaangayak vannee,

**Options (Sinhala → romanized per method):**

- අලසකම වර්ධනය වීම.
  - Phonetic (baseline): alasakama wardhanaya wiima.
  - Aksharamukha: alasakama wardhanaya wiima.
  - Sinhala G2P (phonemic, retains ə): aləsəkəmə wardənəyə wiimə.
  - Sinhala G2P (ASCII, ə→a): alasakama wardanaya wiima.
  - uroman: alasakama vardanaya viima.
- ආත්මාර්ථකාමී කටයුතු කිරීමට යොමු වීම.
  - Phonetic (baseline): aathmaarthakaamii katayuthu kiriimata yomu wiima.
  - Aksharamukha: aatmaarthakaamii katayutu kiriimata yomu wiima.
  - Sinhala G2P (phonemic, retains ə): aatmaartəkaamii katəyutu kiriimətə yomu wiimə.
  - Sinhala G2P (ASCII, ə→a): aatmaartakaamii katayutu kiriimata yomu wiima.
  - uroman: aatmaartakaamii kattayutu kiriimatta yomu viima.
- අසාධාරණය අගය කිරීම.
  - Phonetic (baseline): asaadhaaranaya agaya kiriima.
  - Aksharamukha: asaadhaaranaya agaya kiriima.
  - Sinhala G2P (phonemic, retains ə): asaadaarənəyə agəyə kiriimə.
  - Sinhala G2P (ASCII, ə→a): asaadaaranaya agaya kiriima.
  - uroman: asaadaaranaya agaya kiriima.
- ජය පරාජය සතුටින් විදදරා ගැනීම. ✅
  - Phonetic (baseline): jaya paraajaya sathutin widadaraa gaeniima.
  - Aksharamukha: jaya paraajaya satutin widadaraa gaeniima.
  - Sinhala G2P (phonemic, retains ə): jayə paraajəyə satutin widədəraa gaeniimə.
  - Sinhala G2P (ASCII, ə→a): jaya paraajaya satutin widadaraa gaeniima.
  - uroman: jaya paraajaya satuttin vidadaraa gaeniima.

---

### 15. `mmlu_0865` (Social_Science / Easy)

**Sinhala:** ශ්‍රී ලංකාවේ හා පළල නිවැරදි අනුපිළිවෙලට දැක්වෙන පිළිතුර තෝරන්න.

- **Phonetic (baseline):** shrii lankaawee haa palala niwaeradi anupiliwelata daekwena pilithura thooranna.
- **Aksharamukha:** shrii lankaawee haa palala niwaeradi anupiliwelata daekwena pilitura tooranna.
- **Sinhala G2P (phonemic, retains ə):** shrii langkaawee haa palələ niwaerədi anupiliwelətə daekwenə piliturə toorannə.
- **Sinhala G2P (ASCII, ə→a):** shrii langkaawee haa palala niwaeradi anupiliwelata daekwena pilitura tooranna.
- **uroman:** srii lankaavee haa palala nivaeradi anupilivelatta daekvena pilitura tooranna.

**Options (Sinhala → romanized per method):**

- දිග කි. මී. 224, පළල කි.මී. 433
  - Phonetic (baseline): diga ki. mii. 224, palala ki.mii. 433
  - Aksharamukha: diga ki. mii. 224, palala ki.mii. 433
  - Sinhala G2P (phonemic, retains ə): digə ki. mii. 224, palələ ki.mii. 433
  - Sinhala G2P (ASCII, ə→a): diga ki. mii. 224, palala ki.mii. 433
  - uroman: diga ki. mii. 224, palala ki.mii. 433
- දිග කි.මී. 423, පළල කි.මී 242
  - Phonetic (baseline): diga ki.mii. 423, palala ki.mii 242
  - Aksharamukha: diga ki.mii. 423, palala ki.mii 242
  - Sinhala G2P (phonemic, retains ə): digə ki.mii. 423, palələ ki.mii 242
  - Sinhala G2P (ASCII, ə→a): diga ki.mii. 423, palala ki.mii 242
  - uroman: diga ki.mii. 423, palala ki.mii 242
- දිග කි.මී. 424, පළල කි.මී. 264
  - Phonetic (baseline): diga ki.mii. 424, palala ki.mii. 264
  - Aksharamukha: diga ki.mii. 424, palala ki.mii. 264
  - Sinhala G2P (phonemic, retains ə): digə ki.mii. 424, palələ ki.mii. 264
  - Sinhala G2P (ASCII, ə→a): diga ki.mii. 424, palala ki.mii. 264
  - uroman: diga ki.mii. 424, palala ki.mii. 264
- දිග කි.මී. 432, පළල කි.මී. 224 ✅
  - Phonetic (baseline): diga ki.mii. 432, palala ki.mii. 224
  - Aksharamukha: diga ki.mii. 432, palala ki.mii. 224
  - Sinhala G2P (phonemic, retains ə): digə ki.mii. 432, palələ ki.mii. 224
  - Sinhala G2P (ASCII, ə→a): diga ki.mii. 432, palala ki.mii. 224
  - uroman: diga ki.mii. 432, palala ki.mii. 224

---

### 16. `mmlu_1035` (Social_Science / Easy)

**Sinhala:** 6 ශ්‍රේණියේ ඉගෙනුම ලබන දිනිඳු ගේ ශරීර ස්කන්ධ දර්ශකය යහපත් මට්ටමක පවතින බව සෞඛ්‍ය ගුරුතුමිය පැවසුවාය. වර්ධක සටහනේ ඔහුට අදාල වර්ණය වන්නේ කුමක්ද?

- **Phonetic (baseline):** 6 shreeniyee igenuma labana dinindu gee shariira skandha darshakaya yahapath mattamaka pawathina bawa saukhya guruthumiya paewasuwaaya. wardhaka satahanee ohuta adaala warnaya wannee kumakda?
- **Aksharamukha:** 6 shreeniyee igenuma labana dinindu gee shariira skandha darshakaya yahapat mattamaka pawatina bawa saukhya gurutumiya paewasuwaaya. wardhaka satahanee ohuta adaala warnaya wannee kumakda?
- **Sinhala G2P (phonemic, retains ə):** 6 shreeniyee igenumə labənə dinindu gee shariirə skandə darshəkəyə yahapat mattəməkə pawətinə bawə saukyə gurutumiyə paewəsuwaayə. wardəkə satəhanee ohutə adaalə warnəyə wannee kumakdə?
- **Sinhala G2P (ASCII, ə→a):** 6 shreeniyee igenuma labana dinindu gee shariira skanda darshakaya yahapat mattamaka pawatina bawa saukya gurutumiya paewasuwaaya. wardaka satahanee ohuta adaala warnaya wannee kumakda?
- **uroman:** 6 sreeniyee igenuma labana dinidu gee sariira skanda darsakaya yahapat mattttamaka pavatina bava saukya gurutumiya paevasuvaaya. vardaka sattahanee ohutta adaala varnaya vannee kumakda?

**Options (Sinhala → romanized per method):**

- දම් පාට
  - Phonetic (baseline): dam paata
  - Aksharamukha: dam paata
  - Sinhala G2P (phonemic, retains ə): dam paatə
  - Sinhala G2P (ASCII, ə→a): dam paata
  - uroman: dam paatta
- කොළ පාට ✅
  - Phonetic (baseline): kola paata
  - Aksharamukha: kola paata
  - Sinhala G2P (phonemic, retains ə): kolə paatə
  - Sinhala G2P (ASCII, ə→a): kola paata
  - uroman: kola paatta
- තැඹිලි පාට
  - Phonetic (baseline): thaembili paata
  - Aksharamukha: taembili paata
  - Sinhala G2P (phonemic, retains ə): taembili paatə
  - Sinhala G2P (ASCII, ə→a): taembili paata
  - uroman: taebili paatta
- රතු පාට
  - Phonetic (baseline): rathu paata
  - Aksharamukha: ratu paata
  - Sinhala G2P (phonemic, retains ə): ratu paatə
  - Sinhala G2P (ASCII, ə→a): ratu paata
  - uroman: ratu paatta

---

### 17. `mmlu_1117` (Humanities / Easy)

**Sinhala:** පහත කොටස් නිවැරදිව ගැලපූ විට නිවැරදි පිළිතුර වන්නේ,

1) වෙළඳ සංවිධාන,  2) පේෂ කර්මාන්තය, 3) වරායන් ආශ්‍රිතව කටයුතු කිරීම, 4) ගවයන්ගේ පිටේ බඩු ගෙනයාම
A රෙදිපිළි, B තවලම්, C සුංක, D රේගු නිලධාරීන්

- **Phonetic (baseline):** pahatha kotas niwaeradiwa gaelapuu wita niwaeradi pilithura wannee,

1) welanda sanwidhaana,  2) peesha karmaanthaya, 3) waraayan aashrithawa katayuthu kiriima, 4) gawayangee pitee badu genayaama
A redipili, B thawalam, C sunka, D reegu niladhaariin
- **Aksharamukha:** pahata kotas niwaeradiwa gaelapuu wita niwaeradi pilitura wannee,

1) welanda sanwidhaana,  2) peesha karmaantaya, 3) waraayan aashritawa katayutu kiriima, 4) gawayangee pitee badu genayaama
A redipili, B tawalam, C sunka, D reegu niladhaariin
- **Sinhala G2P (phonemic, retains ə):** pahatə kotas niwaerədiwə gaeləpuu witə niwaerədi piliturə wannee,

1) weləndə sangwidaanə,  2) peeshə karmaantəyə, 3) waraayan aashritəwə katəyutu kiriimə, 4) gawəyangee pitee badu genəyaamə
A redipili, B tawəlam, C sungkə, D reegu nilədaariin
- **Sinhala G2P (ASCII, ə→a):** pahata kotas niwaeradiwa gaelapuu wita niwaeradi pilitura wannee,

1) welanda sangwidaana,  2) peesha karmaantaya, 3) waraayan aashritawa katayutu kiriima, 4) gawayangee pitee badu genayaama
A redipili, B tawalam, C sungka, D reegu niladaariin
- **uroman:** pahata kottas nivaeradiva gaelapuu vitta nivaeradi pilitura vannee,

1) velada sanvidaana,  2) peesa karmaantaya, 3) varaayan aasritava kattayutu kiriima, 4) gavayangee pittee baddu genayaama
A redipili, B tavalam, C sunka, D reegu niladaariin

**Options (Sinhala → romanized per method):**

- ABCD
  - Phonetic (baseline): ABCD
  - Aksharamukha: ABCD
  - Sinhala G2P (phonemic, retains ə): ABCD
  - Sinhala G2P (ASCII, ə→a): ABCD
  - uroman: ABCD
- DEBA
  - Phonetic (baseline): DEBA
  - Aksharamukha: DEBA
  - Sinhala G2P (phonemic, retains ə): DEBA
  - Sinhala G2P (ASCII, ə→a): DEBA
  - uroman: DEBA
- BADC
  - Phonetic (baseline): BADC
  - Aksharamukha: BADC
  - Sinhala G2P (phonemic, retains ə): BADC
  - Sinhala G2P (ASCII, ə→a): BADC
  - uroman: BADC
- CADB ✅
  - Phonetic (baseline): CADB
  - Aksharamukha: CADB
  - Sinhala G2P (phonemic, retains ə): CADB
  - Sinhala G2P (ASCII, ə→a): CADB
  - uroman: CADB

---

### 18. `mmlu_1210` (Humanities / Easy)

**Sinhala:** වුළුහි ෆලු වල ගණන ,


- **Phonetic (baseline):** wuluhi falu wala ganana ,

- **Aksharamukha:** wuluhi falu wala ganana ,

- **Sinhala G2P (phonemic, retains ə):** wuluhi falu walə ganənə ,

- **Sinhala G2P (ASCII, ə→a):** wuluhi falu wala ganana ,

- **uroman:** vuluhi falu vala ganana ,


**Options (Sinhala → romanized per method):**

- 5
  - Phonetic (baseline): 5
  - Aksharamukha: 5
  - Sinhala G2P (phonemic, retains ə): 5
  - Sinhala G2P (ASCII, ə→a): 5
  - uroman: 5
- 7
  - Phonetic (baseline): 7
  - Aksharamukha: 7
  - Sinhala G2P (phonemic, retains ə): 7
  - Sinhala G2P (ASCII, ə→a): 7
  - uroman: 7
- 8
  - Phonetic (baseline): 8
  - Aksharamukha: 8
  - Sinhala G2P (phonemic, retains ə): 8
  - Sinhala G2P (ASCII, ə→a): 8
  - uroman: 8
- 6 ✅
  - Phonetic (baseline): 6
  - Aksharamukha: 6
  - Sinhala G2P (phonemic, retains ə): 6
  - Sinhala G2P (ASCII, ə→a): 6
  - uroman: 6

---

### 19. `mmlu_1233` (Humanities / Easy)

**Sinhala:** නබි නුහ් (අලෛ) තුමාගේ නැව ගොඩ බැස්සූ ස්ථානය,


- **Phonetic (baseline):** nabi nuh (alai) thumaagee naewa goda baessuu sthaanaya,

- **Aksharamukha:** nabi nuh (alai) tumaagee naewa goda baessuu sthaanaya,

- **Sinhala G2P (phonemic, retains ə):** nabi nuh (alai) tumaagee naewə godə baessuu staanəyə,

- **Sinhala G2P (ASCII, ə→a):** nabi nuh (alai) tumaagee naewa goda baessuu staanaya,

- **uroman:** nabi nuh (alai) tumaagee naeva godda baessuu staanaya,


**Options (Sinhala → romanized per method):**

- නූර් කන්ද
  - Phonetic (baseline): nuur kanda
  - Aksharamukha: nuur kanda
  - Sinhala G2P (phonemic, retains ə): nuur kandə
  - Sinhala G2P (ASCII, ə→a): nuur kanda
  - uroman: nuur kanda
- තුර්සිනා කන්ද
  - Phonetic (baseline): thursinaa kanda
  - Aksharamukha: tursinaa kanda
  - Sinhala G2P (phonemic, retains ə): tursinaa kandə
  - Sinhala G2P (ASCII, ə→a): tursinaa kanda
  - uroman: tursinaa kanda
- ජූදි කන්ද ✅
  - Phonetic (baseline): juudi kanda
  - Aksharamukha: juudi kanda
  - Sinhala G2P (phonemic, retains ə): juudi kandə
  - Sinhala G2P (ASCII, ə→a): juudi kanda
  - uroman: juudi kanda
- සෆා කන්ද
  - Phonetic (baseline): safaa kanda
  - Aksharamukha: safaa kanda
  - Sinhala G2P (phonemic, retains ə): safaa kandə
  - Sinhala G2P (ASCII, ə→a): safaa kanda
  - uroman: safaa kanda

---

### 20. `mmlu_1310` (Language / Easy)

**Sinhala:** නූතන සිංහල වර්ණ මාලාවේ සඤ්ඤක අක්ෂර ගණන කීයද?

- **Phonetic (baseline):** nuuthana sinhala warna maalaawee sanynyaka akshara ganana kiiyada?
- **Aksharamukha:** nuutana sinhala warna maalaawee sanynyaka akshara ganana kiiyada?
- **Sinhala G2P (phonemic, retains ə):** nuutənə singhələ warnə maalaawee sanynyəkə akshərə ganənə kiiyədə?
- **Sinhala G2P (ASCII, ə→a):** nuutana singhala warna maalaawee sanynyaka akshara ganana kiiyada?
- **uroman:** nuutana sinhala varna maalaavee sanynyaka aksara ganana kiiyada?

**Options (Sinhala → romanized per method):**

- 10 යි.
  - Phonetic (baseline): 10 yi.
  - Aksharamukha: 10 yi.
  - Sinhala G2P (phonemic, retains ə): 10 yi.
  - Sinhala G2P (ASCII, ə→a): 10 yi.
  - uroman: 10 yi.
- 5 යි. ✅
  - Phonetic (baseline): 5 yi.
  - Aksharamukha: 5 yi.
  - Sinhala G2P (phonemic, retains ə): 5 yi.
  - Sinhala G2P (ASCII, ə→a): 5 yi.
  - uroman: 5 yi.
- 18 යි.
  - Phonetic (baseline): 18 yi.
  - Aksharamukha: 18 yi.
  - Sinhala G2P (phonemic, retains ə): 18 yi.
  - Sinhala G2P (ASCII, ə→a): 18 yi.
  - uroman: 18 yi.
- 3යි.
  - Phonetic (baseline): 3yi.
  - Aksharamukha: 3yi.
  - Sinhala G2P (phonemic, retains ə): 3yi.
  - Sinhala G2P (ASCII, ə→a): 3yi.
  - uroman: 3yi.

---

### 21. `mmlu_1386` (Language / Easy)

**Sinhala:** ඒක වචන අනුක්ත නාම පදයක් වන්නේ ,

- **Phonetic (baseline):** eeka wachana anuktha naama padayak wannee ,
- **Aksharamukha:** eeka wachana anukta naama padayak wannee ,
- **Sinhala G2P (phonemic, retains ə):** eekə wachənə anuktə naamə padəyak wannee ,
- **Sinhala G2P (ASCII, ə→a):** eeka wachana anukta naama padayak wannee ,
- **uroman:** eeka vacana anukta naama padayak vannee ,

**Options (Sinhala → romanized per method):**

- මා ✅
  - Phonetic (baseline): maa
  - Aksharamukha: maa
  - Sinhala G2P (phonemic, retains ə): maa
  - Sinhala G2P (ASCII, ə→a): maa
  - uroman: maa
- ඔවුන්
  - Phonetic (baseline): owun
  - Aksharamukha: owun
  - Sinhala G2P (phonemic, retains ə): oun
  - Sinhala G2P (ASCII, ə→a): oun
  - uroman: ovun
- දියණියක්
  - Phonetic (baseline): diyaniyak
  - Aksharamukha: diyaniyak
  - Sinhala G2P (phonemic, retains ə): diyəniyak
  - Sinhala G2P (ASCII, ə→a): diyaniyak
  - uroman: diyaniyak
- සිංහයෙක්
  - Phonetic (baseline): sinhayek
  - Aksharamukha: sinhayek
  - Sinhala G2P (phonemic, retains ə): singhəyek
  - Sinhala G2P (ASCII, ə→a): singhayek
  - uroman: sinhayek

---

### 22. `mmlu_1509` (Humanities / Easy)

**Sinhala:** තෙයිත තෙයිත තෙයිත යතාම් යන පා සරඹයේ සරඹ නාමය වන්නේ

- **Phonetic (baseline):** theyitha theyitha theyitha yathaam yana paa sarambayee saramba naamaya wannee
- **Aksharamukha:** teyita teyita teyita yataam yana paa sarambayee saramba naamaya wannee
- **Sinhala G2P (phonemic, retains ə):** teitə teitə teitə yataam yanə paa sarəmbəyee sarəmbə naaməyə wannee
- **Sinhala G2P (ASCII, ə→a):** teita teita teita yataam yana paa sarambayee saramba naamaya wannee
- **uroman:** teyita teyita teyita yataam yana paa sarabayee saraba naamaya vannee

**Options (Sinhala → romanized per method):**

- අඩිය
  - Phonetic (baseline): adiya
  - Aksharamukha: adiya
  - Sinhala G2P (phonemic, retains ə): adiyə
  - Sinhala G2P (ASCII, ə→a): adiya
  - uroman: addiya
- දෑඩිය
  - Phonetic (baseline): daaediya
  - Aksharamukha: daaediya
  - Sinhala G2P (phonemic, retains ə): daaediyə
  - Sinhala G2P (ASCII, ə→a): daaediya
  - uroman: daeddiya
- තුන් අඩිය
  - Phonetic (baseline): thun adiya
  - Aksharamukha: tun adiya
  - Sinhala G2P (phonemic, retains ə): tun adiyə
  - Sinhala G2P (ASCII, ə→a): tun adiya
  - uroman: tun addiya
- සිව් අඩිය ✅
  - Phonetic (baseline): siw adiya
  - Aksharamukha: siw adiya
  - Sinhala G2P (phonemic, retains ə): siw adiyə
  - Sinhala G2P (ASCII, ə→a): siw adiya
  - uroman: siv addiya

---

### 23. `mmlu_1517` (Humanities / Easy)

**Sinhala:** මණ්ඩි පද හා පා සරඹ වලින් දැකිය හැකි නර්තන සම්ප්‍රදාය වන්නේ,

- **Phonetic (baseline):** mandi pada haa paa saramba walin daekiya haeki narthana sampradaaya wannee,
- **Aksharamukha:** mandi pada haa paa saramba walin daekiya haeki nartana sampradaaya wannee,
- **Sinhala G2P (phonemic, retains ə):** mandi padə haa paa sarəmbə walin daekiyə haeki nartənə sampradaayə wannee,
- **Sinhala G2P (ASCII, ə→a):** mandi pada haa paa saramba walin daekiya haeki nartana sampradaaya wannee,
- **uroman:** manddi pada haa paa saraba valin daekiya haeki nartana sampradaaya vannee,

**Options (Sinhala → romanized per method):**

- උඩරට හා පහත රට සම්ප්‍රදායන් රට සම්ප්‍රදායන්.
  - Phonetic (baseline): udarata haa pahatha rata sampradaayan rata sampradaayan.
  - Aksharamukha: udarata haa pahata rata sampradaayan rata sampradaayan.
  - Sinhala G2P (phonemic, retains ə): udərətə haa pahatə ratə sampradaayan ratə sampradaayan.
  - Sinhala G2P (ASCII, ə→a): udarata haa pahata rata sampradaayan rata sampradaayan.
  - uroman: uddaratta haa pahata ratta sampradaayan ratta sampradaayan.
- පහතරට සහ උඩරට සම්ප්‍රදායන්. ✅
  - Phonetic (baseline): pahatharata saha udarata sampradaayan.
  - Aksharamukha: pahatarata saha udarata sampradaayan.
  - Sinhala G2P (phonemic, retains ə): pahatərətə saha udərətə sampradaayan.
  - Sinhala G2P (ASCII, ə→a): pahatarata saha udarata sampradaayan.
  - uroman: pahataratta saha uddaratta sampradaayan.
- සබරගමු හා පහතරට සම්ප්‍රදායන්.
  - Phonetic (baseline): sabaragamu haa pahatharata sampradaayan.
  - Aksharamukha: sabaragamu haa pahatarata sampradaayan.
  - Sinhala G2P (phonemic, retains ə): sabərəgəmu haa pahatərətə sampradaayan.
  - Sinhala G2P (ASCII, ə→a): sabaragamu haa pahatarata sampradaayan.
  - uroman: sabaragamu haa pahataratta sampradaayan.
- පහතරට හා උඩරට සම්ප්‍රදායන්.
  - Phonetic (baseline): pahatharata haa udarata sampradaayan.
  - Aksharamukha: pahatarata haa udarata sampradaayan.
  - Sinhala G2P (phonemic, retains ə): pahatərətə haa udərətə sampradaayan.
  - Sinhala G2P (ASCII, ə→a): pahatarata haa udarata sampradaayan.
  - uroman: pahataratta haa uddaratta sampradaayan.

---

### 24. `mmlu_1519` (Humanities / Easy)

**Sinhala:** “හිස මුව තුල බෙල්ල දෙවුර දෑතේ දසැගිලි"

- **Phonetic (baseline):** “hisa muwa thula bella dewura daaethee dasaegili"
- **Aksharamukha:** “hisa muwa tula bella dewura daaetee dasaegili"
- **Sinhala G2P (phonemic, retains ə):** “hisə muwə tulə bellə deurə daaetee dasaegili"
- **Sinhala G2P (ASCII, ə→a):** “hisa muwa tula bella deura daaetee dasaegili"
- **uroman:** “hisa muva tula bella devura daetee dasaegili"

**Options (Sinhala → romanized per method):**

- ලී කෙලි කවියෙකි.
  - Phonetic (baseline): lii keli kawiyeki.
  - Aksharamukha: lii keli kawiyeki.
  - Sinhala G2P (phonemic, retains ə): lii keli kawiyeki.
  - Sinhala G2P (ASCII, ə→a): lii keli kawiyeki.
  - uroman: lii keli kaviyeki.
- සවරං කවියකි.
  - Phonetic (baseline): sawaran kawiyaki.
  - Aksharamukha: sawaran kawiyaki.
  - Sinhala G2P (phonemic, retains ə): sawərang kawiyəki.
  - Sinhala G2P (ASCII, ə→a): sawarang kawiyaki.
  - uroman: savaran kaviyaki.
- සිරසපාද කවියකි. ✅
  - Phonetic (baseline): sirasapaada kawiyaki.
  - Aksharamukha: sirasapaada kawiyaki.
  - Sinhala G2P (phonemic, retains ə): sirəsəpaadə kawiyəki.
  - Sinhala G2P (ASCII, ə→a): sirasapaada kawiyaki.
  - uroman: sirasapaada kaviyaki.
- පතුරු කවියකි.
  - Phonetic (baseline): pathuru kawiyaki.
  - Aksharamukha: paturu kawiyaki.
  - Sinhala G2P (phonemic, retains ə): paturu kawiyəki.
  - Sinhala G2P (ASCII, ə→a): paturu kawiyaki.
  - uroman: paturu kaviyaki.

---

### 25. `mmlu_1828` (Stem / Easy)

**Sinhala:** රසායනික විපර්යාසයක දී සිදු නොවිය හැක්කේ කුමක්ද?

- **Phonetic (baseline):** rasaayanika wiparyaasayaka dii sidu nowiya haekkee kumakda?
- **Aksharamukha:** rasaayanika wiparyaasayaka dii sidu nowiya haekkee kumakda?
- **Sinhala G2P (phonemic, retains ə):** rasaayənikə wiparyaasəyəkə dii sidu nowiyə haekkee kumakdə?
- **Sinhala G2P (ASCII, ə→a):** rasaayanika wiparyaasayaka dii sidu nowiya haekkee kumakda?
- **uroman:** rasaayanika viparyaasayaka dii sidu noviya haekkee kumakda?

**Options (Sinhala → romanized per method):**

- භෞතික අවස්ථාව පමණක් වෙනස් වීම ✅
  - Phonetic (baseline): bhauthika awasthaawa pamanak wenas wiima
  - Aksharamukha: bhautika awasthaawa pamanak wenas wiima
  - Sinhala G2P (phonemic, retains ə): bautikə awastaawə pamənak wenas wiimə
  - Sinhala G2P (ASCII, ə→a): bautika awastaawa pamanak wenas wiima
  - uroman: bautika avastaava pamanak venas viima
- තාපය පිට වීම
  - Phonetic (baseline): thaapaya pita wiima
  - Aksharamukha: taapaya pita wiima
  - Sinhala G2P (phonemic, retains ə): taapəyə pitə wiimə
  - Sinhala G2P (ASCII, ə→a): taapaya pita wiima
  - uroman: taapaya pitta viima
- වායු බුබුලු පිටවීම
  - Phonetic (baseline): waayu bubulu pitawiima
  - Aksharamukha: waayu bubulu pitawiima
  - Sinhala G2P (phonemic, retains ə): waayu bubulu pitəwiimə
  - Sinhala G2P (ASCII, ə→a): waayu bubulu pitawiima
  - uroman: vaayu bubulu pittaviima
- වර්ණය වෙනස් වීම
  - Phonetic (baseline): warnaya wenas wiima
  - Aksharamukha: warnaya wenas wiima
  - Sinhala G2P (phonemic, retains ə): warnəyə wenas wiimə
  - Sinhala G2P (ASCII, ə→a): warnaya wenas wiima
  - uroman: varnaya venas viima

---

## SOLD samples

### 1. `sold_0027` (label: NOT)

**Sinhala:** යාපනේ A32,A9 , නාගදීපෙට යන පාර, පෙදුරු තුඩු පාර හෙම  හොඳ යි.අනික් එහෙ පාරවල් ගොඩක් සවුත්තු. අතුරුපාරවල් ගන්න දෙයක් නෑ.AB-21 වගේ පාරවලුත් පෙලක් තැන් පට්ට සවුත්තු. සිංගල මුනියා යාපන ටවුමට නාගදීපෙට ගිහින් ඇවිල්ල අහනො මොනා තා එහෙ කෙරෙන්නෙ ඕනි කියල ?

- **Phonetic (baseline):** yaapanee A32,A9 , naagadiipeta yana paara, peduru thudu paara hema  honda yi.anik ehe paarawal godak sawuththu. athurupaarawal ganna deyak naae.AB-21 wagee paarawaluth pelak thaen patta sawuththu. singala muniyaa yaapana tawumata naagadiipeta gihin aewilla ahano monaa thaa ehe kerenne ooni kiyala ?
- **Aksharamukha:** yaapanee A32,A9 , naagadiipeta yana paara, peduru tudu paara hema  honda yi.anik ehe paarawal godak sawuttu. aturupaarawal ganna deyak naae.AB-21 wagee paarawalut pelak taen patta sawuttu. singala muniyaa yaapana tawumata naagadiipeta gihin aewilla ahano monaa taa ehe kerenne ooni kiyala ?
- **Sinhala G2P (phonemic, retains ə):** yaapənee A32,A9 , naagədiipetə yanə paarə, peduru tudu paarə hemə  hondə yi.anik ehe paarəwal godak sauttu. aturupaarəwal gannə deyak naae.AB-21 wagee paarəwəlut pelak taen pattə sauttu. singgələ muniyaa yaapənə taumətə naagədiipetə gihin aewillə ahano monaa taa ehe kerenne ooni kiyələ ?
- **Sinhala G2P (ASCII, ə→a):** yaapanee A32,A9 , naagadiipeta yana paara, peduru tudu paara hema  honda yi.anik ehe paarawal godak sauttu. aturupaarawal ganna deyak naae.AB-21 wagee paarawalut pelak taen patta sauttu. singgala muniyaa yaapana taumata naagadiipeta gihin aewilla ahano monaa taa ehe kerenne ooni kiyala ?
- **uroman:** yaapanee A32,A9 , naagadiipetta yana paara, peduru tuddu paara hema  hoda yi.anik ehe paaraval goddak savuttu. aturupaaraval ganna deyak nae.AB-21 vagee paaravalut pelak taen patttta savuttu. singala muniyaa yaapana ttavumatta naagadiipetta gihin aevilla ahano monaa taa ehe kerenne ooni kiyala ?

---

### 2. `sold_0178` (label: NOT)

**Sinhala:** @USER අද මම ඔබ වෙනුවෙන් බැල්ලිගෙ ඉන්නේ, මට හතර නැරැඹීමේ, මගේ පස්ස මත මට පහර, මගේ මුහුණ මත මගේ ගැසුවහොත් ඔබ මගේ බලු පැටියෙක් කියනවා නම්

- **Phonetic (baseline):** @USER ada mama oba wenuwen baellige innee, mata hathara naeraembiimee, magee passa matha mata pahara, magee muhuna matha magee gaesuwahoth oba magee balu paetiyek kiyanawaa nam
- **Aksharamukha:** @USER ada mama oba wenuwen baellige innee, mata hatara naeraembiimee, magee passa mata mata pahara, magee muhuna mata magee gaesuwahot oba magee balu paetiyek kiyanawaa nam
- **Sinhala G2P (phonemic, retains ə):** @USER adə mamə obə wenuwen baellige innee, matə hatərə naeraembiimee, magee passə matə matə paharə, magee muhunə matə magee gaesuwəhot obə magee balu paetiyek kiyənəwaa nam
- **Sinhala G2P (ASCII, ə→a):** @USER ada mama oba wenuwen baellige innee, mata hatara naeraembiimee, magee passa mata mata pahara, magee muhuna mata magee gaesuwahot oba magee balu paetiyek kiyanawaa nam
- **uroman:** @USER ada mama oba venuven baellige innee, matta hatara naeraebiimee, magee passa mata matta pahara, magee muhuna mata magee gaesuvahot oba magee balu paettiyek kiyanavaa nam

---

### 3. `sold_0380` (label: OFF)

**Sinhala:** යකෙක් කියලා දන්නවනම් පුකටද ඕයි පස්සෙන් ආවේ ???  #YouClaimedWarBitch #හුජ්ජ_කෙල්ලෝ

- **Phonetic (baseline):** yakek kiyalaa dannawanam pukatada ooyi passen aawee ???  #YouClaimedWarBitch #hujja_kelloo
- **Aksharamukha:** yakek kiyalaa dannawanam pukatada ooyi passen aawee ???  #YouClaimedWarBitch #hujja_kelloo
- **Sinhala G2P (phonemic, retains ə):** yakek kiyəlaa dannəwənam pukətədə ooyi passen aawee ???  #YouClaimedWarBitch #hujjə_kelloo
- **Sinhala G2P (ASCII, ə→a):** yakek kiyalaa dannawanam pukatada ooyi passen aawee ???  #YouClaimedWarBitch #hujja_kelloo
- **uroman:** yakek kiyalaa dannavanam pukattada ooyi passen aavee ???  #YouClaimedWarBitch #hujja_kelloo

---

### 4. `sold_0397` (label: NOT)

**Sinhala:** ගොනා කන පැලේ ගොන් පැලේ නැතිනම් රජ පැලේද?

- **Phonetic (baseline):** gonaa kana paelee gon paelee naethinam raja paeleeda?
- **Aksharamukha:** gonaa kana paelee gon paelee naetinam raja paeleeda?
- **Sinhala G2P (phonemic, retains ə):** gonaa kanə paelee gon paelee naetinam rajə paeleedə?
- **Sinhala G2P (ASCII, ə→a):** gonaa kana paelee gon paelee naetinam raja paeleeda?
- **uroman:** gonaa kana paelee gon paelee naetinam raja paeleeda?

---

### 5. `sold_0419` (label: OFF)

**Sinhala:** @USER මේ පකයෝ ⁣අම්මට  මිනිස්සු පාවලා දෙන්නේ තෝ පකය අවජාතක අම්ම තාත්ත නැතිව උපන්න පොන්නයෙක්ද හුත්තෝ

- **Phonetic (baseline):** @USER mee pakayoo ⁣ammata  minissu paawalaa dennee thoo pakaya awajaathaka amma thaaththa naethiwa upanna ponnayekda huththoo
- **Aksharamukha:** @USER mee pakayoo ⁣ammata  minissu paawalaa dennee too pakaya awajaataka amma taatta naetiwa upanna ponnayekda huttoo
- **Sinhala G2P (phonemic, retains ə):** @USER mee pakəyoo ⁣ammətə  minissu paawəlaa dennee too pakəyə awəjaatəkə ammə taattə naetiwə upannə ponnəyekdə huttoo
- **Sinhala G2P (ASCII, ə→a):** @USER mee pakayoo ⁣ammata  minissu paawalaa dennee too pakaya awajaataka amma taatta naetiwa upanna ponnayekda huttoo
- **uroman:** @USER mee pakayoo ⁣ammatta  minissu paavalaa dennee too pakaya avajaataka amma taatta naetiva upanna ponnayekda huttoo

---

### 6. `sold_0637` (label: OFF)

**Sinhala:** @USER ටෙෳකන්න ඕයි බිජ්ජ කපන් වැලලෙන්න හිතෙනවා කියන කතා වලට @USER  @USER

- **Phonetic (baseline):** @USER teluukanna ooyi bijja kapan waelalenna hithenawaa kiyana kathaa walata @USER  @USER
- **Aksharamukha:** @USER teluukanna ooyi bijja kapan waelalenna hitenawaa kiyana kataa walata @USER  @USER
- **Sinhala G2P (phonemic, retains ə):** @USER teluukannə ooyi bijjə kapan waeləlennə hitenəwaa kiyənə kataa walətə @USER  @USER
- **Sinhala G2P (ASCII, ə→a):** @USER teluukanna ooyi bijja kapan waelalenna hitenawaa kiyana kataa walata @USER  @USER
- **uroman:** @USER tteluukanna ooyi bijja kapan vaelalenna hitenavaa kiyana kataa valatta @USER  @USER

---

### 7. `sold_0654` (label: OFF)

**Sinhala:** @USER කකුල් දෙක මැදින් බිජ්ජ උල් වෙලා වගෙ

- **Phonetic (baseline):** @USER kakul deka maedin bijja ul welaa wage
- **Aksharamukha:** @USER kakul deka maedin bijja ul welaa wage
- **Sinhala G2P (phonemic, retains ə):** @USER kakul dekə maedin bijjə ul welaa wage
- **Sinhala G2P (ASCII, ə→a):** @USER kakul deka maedin bijja ul welaa wage
- **uroman:** @USER kakul deka maedin bijja ul velaa vage

---

### 8. `sold_0815` (label: NOT)

**Sinhala:** එස් එම් එස් පෙන්නාපං වට්ස් ඇප් එක ඔන් කරපං  චැට් බොක්ස් එක පෙන්නාපං ස්පීකර් ෆෝන් එක දාපං   ෂෝර්ට් ස්කර්ට්ස් විසි කරපං ෂෝස් දැමිලි නවත්තපං චීස් සිනා කට් කරපං   ස්වීට් හාර්ට් ලෙස ඉඳපං  කොටු පනින්න මට දීපං  මගෙ වගතුග නොඅසාපං මං ජේලර් බව දැනගං තොගෙ කූඩුවෙ තෝ ඉඳපං  සෙප්‍රනෝ ඔකියෝපියර්ස්  @USER  · 10 Dec 2017 මං ගැන විතරක් හිතපං අයිතිය මගෙ බව හිතපං  පත්තිනි චරිතය රැකපං  එළි වෙනකං හොටු පෙරපං   ඉන්නේ කොතනද කියපං  කවුරුත් එක්කද කියපං  ඌට ෆෝන් එක දීපං  දැන් ඔය ඇති කට වහපං   ~උපුටා ගැනීමක්~ කතෲට සියලු ගෞරවය හිමිවිය යුතුය...

- **Phonetic (baseline):** es em es pennaapan wats aep eka on karapan  chaet boks eka pennaapan spiikar foon eka daapan   shoort skarts wisi karapan shoos daemili nawaththapan chiis sinaa kat karapan   swiit haart lesa indapan  kotu paninna mata diipan  mage wagathuga noasaapan man jeelar bawa daenagan thoge kuuduwe thoo indapan  sepranoo okiyoopiyars  @USER  · 10 Dec 2017 man gaena witharak hithapan ayithiya mage bawa hithapan  paththini charithaya raekapan  eli wenakan hotu perapan   innee kothanada kiyapan  kawuruth ekkada kiyapan  uuta foon eka diipan  daen oya aethi kata wahapan   ~uputaa gaeniimak~ kathruuta siyalu gaurawaya himiwiya yuthuya...
- **Aksharamukha:** es em es pennaapan wats aep eka on karapan  chaet boks eka pennaapan spiikar foon eka daapan   shoort skarts wisi karapan shoos daemili nawattapan chiis sinaa kat karapan   swiit haart lesa indapan  kotu paninna mata diipan  mage wagatuga noasaapan man jeelar bawa daenagan toge kuuduwe too indapan  sepranoo okiyoopiyars  @USER  · 10 Dec 2017 man gaena witarak hitapan ayitiya mage bawa hitapan  pattini charitaya raekapan  eli wenakan hotu perapan   innee kotanada kiyapan  kawurut ekkada kiyapan  uuta foon eka diipan  daen oya aeti kata wahapan   ~uputaa gaeniimak~ katruuta siyalu gaurawaya himiwiya yutuya...
- **Sinhala G2P (phonemic, retains ə):** es em es pennaapang wats aep ekə on kərəpang  chaet boks ekə pennaapang spiikər foon ekə daapang   shoort skarts wisi kərəpang shoos daemili nawattəpang chiis sinaa kat kərəpang   swiit haart lesə indəpang  kotu paninnə matə diipang  mage wagətugə noasaapang mang jeelər bawə daenəgang toge kuuduwe too indəpang  sepranoo okiyoopiyars  @USER  · 10 Dec 2017 mang gaenə witərak hitəpang aitiyə mage bawə hitəpang  pattini charitəyə raekəpang  eli wenəkang hotu perəpang   innee kotənədə kiyəpang  kaurut ekkədə kiyəpang  uutə foon ekə diipang  daen oyə aeti katə wahapang   ~uputaa gaeniimak~ katruutə siyəlu gaurəwəyə himiwiyə yutuyə...
- **Sinhala G2P (ASCII, ə→a):** es em es pennaapang wats aep eka on karapang  chaet boks eka pennaapang spiikar foon eka daapang   shoort skarts wisi karapang shoos daemili nawattapang chiis sinaa kat karapang   swiit haart lesa indapang  kotu paninna mata diipang  mage wagatuga noasaapang mang jeelar bawa daenagang toge kuuduwe too indapang  sepranoo okiyoopiyars  @USER  · 10 Dec 2017 mang gaena witarak hitapang aitiya mage bawa hitapang  pattini charitaya raekapang  eli wenakang hotu perapang   innee kotanada kiyapang  kaurut ekkada kiyapang  uuta foon eka diipang  daen oya aeti kata wahapang   ~uputaa gaeniimak~ katruuta siyalu gaurawaya himiwiya yutuya...
- **uroman:** es em es pennaapan vatts aep eka on karapan  caett boks eka pennaapan spiikar foon eka daapan   soortt skartts visi karapan soos daemili navattapan ciis sinaa katt karapan   sviitt haartt lesa idapan  kottu paninna matta diipan  mage vagatuga noasaapan man jeelar bava daenagan toge kuudduve too idapan  sepranoo okiyoopiyars  @USER  · 10 Dec 2017 man gaena vitarak hitapan ayitiya mage bava hitapan  pattini caritaya raekapan  eli venakan hottu perapan   innee kotanada kiyapan  kavurut ekkada kiyapan  uutta foon eka diipan  daen oya aeti katta vahapan   ~uputtaa gaeniimak~ katrratta siyalu gauravaya himiviya yutuya...

---

### 9. `sold_0882` (label: OFF)

**Sinhala:** මේ සක්කිලි කෝච්චි ස්ට්‍රයික් එක කරනව වගේ වැඩ කරද්දි අමාරුවෙන් එදා වේල හොයන් ඉක්මනට ගෙවල් බලන් යන්න ඉන්න මිනිස්සු ඒකාධිපතියො ඉල්ලන එක සාධාරණයි.  ප.ලි. සාමාන්‍ය ජනයා ඉහත ආකල්පය වැරදි ලෙස දකින "ඔබ" තරම් බුද්ධිමත් නැත. "ඔබ" තරම් ධනවත් නැත. රෙද්ද උස්සන් එන්න කලින් සිතන්න.

- **Phonetic (baseline):** mee sakkili koochchi strayik eka karanawa wagee waeda karaddi amaaruwen edaa weela hoyan ikmanata gewal balan yanna inna minissu eekaadhipathiyo illana eka saadhaaranayi.  pa.li. saamaanya janayaa ihatha aakalpaya waeradi lesa dakina "oba" tharam buddhimath naetha. "oba" tharam dhanawath naetha. redda ussan enna kalin sithanna.
- **Aksharamukha:** mee sakkili koochchi strayik eka karanawa wagee waeda karaddi amaaruwen edaa weela hoyan ikmanata gewal balan yanna inna minissu eekaadhipatiyo illana eka saadhaaranayi.  pa.li. saamaanya janayaa ihata aakalpaya waeradi lesa dakina "oba" taram buddhimat naeta. "oba" taram dhanawat naeta. redda ussan enna kalin sitanna.
- **Sinhala G2P (phonemic, retains ə):** mee sakkili koochchi strəyik ekə kərənəwə wagee waedə kəraddi amaaruwen edaa weelə hoyan ikmənətə gewal balan yannə innə minissu eekaadipətiyo illənə ekə saadaarənai.  pə.li. saamaanyə janəyaa ihətə aakalpəyə waerədi lesə dakinə "obə" taram buddimat naetə. "obə" taram danəwat naetə. reddə ussan ennə kalin sitannə.
- **Sinhala G2P (ASCII, ə→a):** mee sakkili koochchi strayik eka karanawa wagee waeda karaddi amaaruwen edaa weela hoyan ikmanata gewal balan yanna inna minissu eekaadipatiyo illana eka saadaaranai.  pa.li. saamaanya janayaa ihata aakalpaya waeradi lesa dakina "oba" taram buddimat naeta. "oba" taram danawat naeta. redda ussan enna kalin sitanna.
- **uroman:** mee sakkili koocci sttrayik eka karanava vagee vaedda karaddi amaaruven edaa veela hoyan ikmanatta geval balan yanna inna minissu eekaadipatiyo illana eka saadaaranayi.  pa.li. saamaanya janayaa ihata aakalpaya vaeradi lesa dakina "oba" taram buddimat naeta. "oba" taram danavat naeta. redda ussan enna kalin sitanna.

---

### 10. `sold_0903` (label: OFF)

**Sinhala:** @USER අගමැටි අහවල් ලබ්බක් කරන්නද යන්නේ??

- **Phonetic (baseline):** @USER agamaeti ahawal labbak karannada yannee??
- **Aksharamukha:** @USER agamaeti ahawal labbak karannada yannee??
- **Sinhala G2P (phonemic, retains ə):** @USER agəmaeti ahawal labbak kərannədə yannee??
- **Sinhala G2P (ASCII, ə→a):** @USER agamaeti ahawal labbak karannada yannee??
- **uroman:** @USER agamaetti ahaval labbak karannada yannee??

---

### 11. `sold_1084` (label: OFF)

**Sinhala:** ඔය ගොන් මොරාල් එවුන් එක්ක ඔච්චර පැටලෙන්න යන්න එපා. ඔය වගේ මෝඩ යක්කු තමයි මොකක් හරි ගොන් තෙලක් වැදුනම සහරාන්ලා වගේ මරාගෙන මැරෙන්න යන්නෙ

- **Phonetic (baseline):** oya gon moraal ewun ekka ochchara paetalenna yanna epaa. oya wagee mooda yakku thamayi mokak hari gon thelak waedunama saharaanlaa wagee maraagena maerenna yanne
- **Aksharamukha:** oya gon moraal ewun ekka ochchara paetalenna yanna epaa. oya wagee mooda yakku tamayi mokak hari gon telak waedunama saharaanlaa wagee maraagena maerenna yanne
- **Sinhala G2P (phonemic, retains ə):** oyə gon moraal eun ekkə ochchərə paetəlennə yannə epaa. oyə wagee moodə yakku tamai mokak hari gon telak waedunəmə saharaanlaa wagee maraagenə maerennə yanne
- **Sinhala G2P (ASCII, ə→a):** oya gon moraal eun ekka ochchara paetalenna yanna epaa. oya wagee mooda yakku tamai mokak hari gon telak waedunama saharaanlaa wagee maraagena maerenna yanne
- **uroman:** oya gon moraal evun ekka occara paettalenna yanna epaa. oya vagee moodda yakku tamayi mokak hari gon telak vaedunama saharaanlaa vagee maraagena maerenna yanne

---

### 12. `sold_1139` (label: NOT)

**Sinhala:** @USER @USER  මුට කෑල්ල බූලක් දීලා දැං පිස්සු හැදිලා

- **Phonetic (baseline):** @USER @USER  muta kaaella buulak diilaa daen pissu haedilaa
- **Aksharamukha:** @USER @USER  muta kaaella buulak diilaa daen pissu haedilaa
- **Sinhala G2P (phonemic, retains ə):** @USER @USER  mutə kaaellə buulak diilaa daeng pissu haedilaa
- **Sinhala G2P (ASCII, ə→a):** @USER @USER  muta kaaella buulak diilaa daeng pissu haedilaa
- **uroman:** @USER @USER  mutta kaella buulak diilaa daen pissu haedilaa

---

### 13. `sold_1140` (label: NOT)

**Sinhala:** @USER ඔයා මට පිස්සා කියල බනිනවනෙ. #අමිත්බනිනවාSL ඒ නිසා මං අද සද්ද කරන්නෑ.

- **Phonetic (baseline):** @USER oyaa mata pissaa kiyala baninawane. #amithbaninawaaSL ee nisaa man ada sadda karannaae.
- **Aksharamukha:** @USER oyaa mata pissaa kiyala baninawane. #amitbaninawaaSL ee nisaa man ada sadda karannaae.
- **Sinhala G2P (phonemic, retains ə):** @USER oyaa matə pissaa kiyələ baninəwəne. #amitbəninəwaaSL ee nisaa mang adə saddə kərannaae.
- **Sinhala G2P (ASCII, ə→a):** @USER oyaa mata pissaa kiyala baninawane. #amitbaninawaaSL ee nisaa mang ada sadda karannaae.
- **uroman:** @USER oyaa matta pissaa kiyala baninavane. #amitbaninavaaSL ee nisaa man ada sadda karannae.

---

### 14. `sold_1379` (label: NOT)

**Sinhala:** ෆේස්බුක් වෝල් එකේ එක එකාට කඩේ යන්නෑ උන් කියන කියන පලියට.  ගොනා වික්කා.

- **Phonetic (baseline):** feesbuk wool ekee eka ekaata kadee yannaae un kiyana kiyana paliyata.  gonaa wikkaa.
- **Aksharamukha:** feesbuk wool ekee eka ekaata kadee yannaae un kiyana kiyana paliyata.  gonaa wikkaa.
- **Sinhala G2P (phonemic, retains ə):** feesbuk wool ekee ekə ekaatə kadee yannaae un kiyənə kiyənə paliyətə.  gonaa wikkaa.
- **Sinhala G2P (ASCII, ə→a):** feesbuk wool ekee eka ekaata kadee yannaae un kiyana kiyana paliyata.  gonaa wikkaa.
- **uroman:** feesbuk vool ekee eka ekaatta kaddee yannae un kiyana kiyana paliyatta.  gonaa vikkaa.

---

### 15. `sold_1394` (label: NOT)

**Sinhala:** @USER @USER  නොදකින් කියන හැටි ඒක

- **Phonetic (baseline):** @USER @USER  nodakin kiyana haeti eeka
- **Aksharamukha:** @USER @USER  nodakin kiyana haeti eeka
- **Sinhala G2P (phonemic, retains ə):** @USER @USER  nodəkin kiyənə haeti eekə
- **Sinhala G2P (ASCII, ə→a):** @USER @USER  nodakin kiyana haeti eeka
- **uroman:** @USER @USER  nodakin kiyana haetti eeka

---

### 16. `sold_1409` (label: OFF)

**Sinhala:** හුකවනවා පකයට මට උබ එවන්නෙ මගුලද පකෝ

- **Phonetic (baseline):** hukawanawaa pakayata mata uba ewanne magulada pakoo
- **Aksharamukha:** hukawanawaa pakayata mata uba ewanne magulada pakoo
- **Sinhala G2P (phonemic, retains ə):** hukəwənəwaa pakəyətə matə ubə ewanne magulədə pakoo
- **Sinhala G2P (ASCII, ə→a):** hukawanawaa pakayata mata uba ewanne magulada pakoo
- **uroman:** hukavanavaa pakayatta matta uba evanne magulada pakoo

---

### 17. `sold_1471` (label: OFF)

**Sinhala:** @USER උබ වගේ පොන්න යක්කුන්ට රිප්ලයි කරන්න වෙලාවක් මට නෑ බන්.. උබේ පුස් කාපු ඇට දෙකේ ගලක් එල්ලන් මූදට පැනපන්.. ඕව තිබුනත් වැඩක් නෑනෙ.. උබල වගේ උන් මේ රටට බරක්.. ඒ නිසා අපිට පව් නොදී මැරියන්..

- **Phonetic (baseline):** @USER uba wagee ponna yakkunta riplayi karanna welaawak mata naae ban.. ubee pus kaapu aeta dekee galak ellan muudata paenapan.. oowa thibunath waedak naaene.. ubala wagee un mee ratata barak.. ee nisaa apita paw nodii maeriyan..
- **Aksharamukha:** @USER uba wagee ponna yakkunta riplayi karanna welaawak mata naae ban.. ubee pus kaapu aeta dekee galak ellan muudata paenapan.. oowa tibunat waedak naaene.. ubala wagee un mee ratata barak.. ee nisaa apita paw nodii maeriyan..
- **Sinhala G2P (phonemic, retains ə):** @USER ubə wagee ponnə yakkuntə riplai kərannə welaawak matə naae ban.. ubee pus kaapu aetə dekee galak ellan muudətə paenəpan.. oowə tibunat waedak naaene.. ubələ wagee un mee ratətə barak.. ee nisaa apitə paw nodii maeriyan..
- **Sinhala G2P (ASCII, ə→a):** @USER uba wagee ponna yakkunta riplai karanna welaawak mata naae ban.. ubee pus kaapu aeta dekee galak ellan muudata paenapan.. oowa tibunat waedak naaene.. ubala wagee un mee ratata barak.. ee nisaa apita paw nodii maeriyan..
- **uroman:** @USER uba vagee ponna yakkuntta riplayi karanna velaavak matta nae ban.. ubee pus kaapu aetta dekee galak ellan muudatta paenapan.. oova tibunat vaeddak naene.. ubala vagee un mee rattatta barak.. ee nisaa apitta pav nodii maeriyan..

---

### 18. `sold_1557` (label: OFF)

**Sinhala:** රෙද්ද කුණු අවුස්සන්නැතුව පලයන්කෝ මගුල

- **Phonetic (baseline):** redda kunu awussannaethuwa palayankoo magula
- **Aksharamukha:** redda kunu awussannaetuwa palayankoo magula
- **Sinhala G2P (phonemic, retains ə):** reddə kunu aussannaetuwə paləyankoo magulə
- **Sinhala G2P (ASCII, ə→a):** redda kunu aussannaetuwa palayankoo magula
- **uroman:** redda kunu avussannaetuva palayankoo magula

---

### 19. `sold_1719` (label: NOT)

**Sinhala:** 96.1 or 96.3 Hiru Fm Islandwide ------------------------------------------ පිඹුරෙක් තත්පර ගානකින් එක කටට මුවෙක්... URL

- **Phonetic (baseline):** 96.1 or 96.3 Hiru Fm Islandwide ------------------------------------------ pimburek thathpara gaanakin eka katata muwek... URL
- **Aksharamukha:** 96.1 or 96.3 Hiru Fm Islandwide ------------------------------------------ pimburek tatpara gaanakin eka katata muwek... URL
- **Sinhala G2P (phonemic, retains ə):** 96.1 or 96.3 Hiru Fm Islandwide ------------------------------------------ pimburek tatpərə gaanəkin ekə katətə muwek... URL
- **Sinhala G2P (ASCII, ə→a):** 96.1 or 96.3 Hiru Fm Islandwide ------------------------------------------ pimburek tatpara gaanakin eka katata muwek... URL
- **uroman:** 96.1 or 96.3 Hiru Fm Islandwide ------------------------------------------ piburek tatpara gaanakin eka kattatta muvek... URL

---

### 20. `sold_1732` (label: OFF)

**Sinhala:** කොන්දක් නැතී ගොන් බිජ්ජෝ බන් -Dang Shapada @USER  · 14 Dec 2018 Twitter එකේ ප්‍රශ්නයක් උනොත් කාත් එක්ක හරි ලඟ ඉදන් පිහියෙන් අනින්න බලන් ඉන්න උන් අඳුර ගන්න පුලුවන්..

- **Phonetic (baseline):** kondak naethii gon bijjoo ban -Dang Shapada @USER  · 14 Dec 2018 Twitter ekee prashnayak unoth kaath ekka hari langa idan pihiyen aninna balan inna un andura ganna puluwan..
- **Aksharamukha:** kondak naetii gon bijjoo ban -Dang Shapada @USER  · 14 Dec 2018 Twitter ekee prashnayak unot kaat ekka hari langa idan pihiyen aninna balan inna un andura ganna puluwan..
- **Sinhala G2P (phonemic, retains ə):** kondak naetii gon bijjoo ban -Dang Shapada @USER  · 14 Dec 2018 Twitter ekee prashnəyak unot kaat ekkə hari langə idan pihiyen aninnə balan innə un andurə gannə puluwan..
- **Sinhala G2P (ASCII, ə→a):** kondak naetii gon bijjoo ban -Dang Shapada @USER  · 14 Dec 2018 Twitter ekee prashnayak unot kaat ekka hari langa idan pihiyen aninna balan inna un andura ganna puluwan..
- **uroman:** kondak naetii gon bijjoo ban -Dang Shapada @USER  · 14 Dec 2018 Twitter ekee prasnayak unot kaat ekka hari laga idan pihiyen aninna balan inna un adura ganna puluvan..

---

### 21. `sold_1840` (label: OFF)

**Sinhala:** @USER @USER  @USER  යකෝ මේ යකා පස්ස පැත්තෙන්ද මේ කතා කියන්නේ

- **Phonetic (baseline):** @USER @USER  @USER  yakoo mee yakaa passa paeththenda mee kathaa kiyannee
- **Aksharamukha:** @USER @USER  @USER  yakoo mee yakaa passa paettenda mee kataa kiyannee
- **Sinhala G2P (phonemic, retains ə):** @USER @USER  @USER  yakoo mee yakaa passə paettendə mee kataa kiyannee
- **Sinhala G2P (ASCII, ə→a):** @USER @USER  @USER  yakoo mee yakaa passa paettenda mee kataa kiyannee
- **uroman:** @USER @USER  @USER  yakoo mee yakaa passa paettenda mee kataa kiyannee

---

### 22. `sold_2233` (label: OFF)

**Sinhala:** @USER ,  @USER  @USER ත්‍රස්ත බෙදුම්වාදීන් මේ ගෑණි නහුතෙට ඩොලර් වලින් පුරවලා නටවන්නේ ලංකාවට තියුණු විදිහට පහර ගහන්න....  ගෑණිගේ නියම වංශය නම් සිංහල බෞද්ධ වෙන්න බැහැ ...'ඔසරිය' බොරු කවර් එකක් වෙන්න පුළුවන්... සිංහල උච්චාරණය බැරි මොකද 'මැණිකේට'?

- **Phonetic (baseline):** @USER ,  @USER  @USER thrastha bedumwaadiin mee gaaeni nahutheta dolar walin purawalaa natawannee lankaawata thiyunu widihata pahara gahanna....  gaaenigee niyama wanshaya nam sinhala bauddha wenna baehae ...'osariya' boru kawar ekak wenna puluwan... sinhala uchchaaranaya baeri mokada 'maenikeeta'?
- **Aksharamukha:** @USER ,  @USER  @USER trasta bedumwaadiin mee gaaeni nahuteta dolar walin purawalaa natawannee lankaawata tiyunu widihata pahara gahanna....  gaaenigee niyama wanshaya nam sinhala bauddha wenna baehae ...'osariya' boru kawar ekak wenna puluwan... sinhala uchchaaranaya baeri mokada 'maenikeeta'?
- **Sinhala G2P (phonemic, retains ə):** @USER ,  @USER  @USER trastə bedumwaadiin mee gaaeni nahutetə dolər walin purəwəlaa natəwannee langkaawətə tiyunu widihətə paharə gahannə....  gaaenigee niyəmə wangshəyə nam singhələ bauddə wennə baehae ...'osəriyə' boru kawər ekak wennə puluwan... singhələ uchchaarənəyə baeri mokədə 'maenikeetə'?
- **Sinhala G2P (ASCII, ə→a):** @USER ,  @USER  @USER trasta bedumwaadiin mee gaaeni nahuteta dolar walin purawalaa natawannee langkaawata tiyunu widihata pahara gahanna....  gaaenigee niyama wangshaya nam singhala baudda wenna baehae ...'osariya' boru kawar ekak wenna puluwan... singhala uchchaaranaya baeri mokada 'maenikeeta'?
- **uroman:** @USER ,  @USER  @USER trasta bedumvaadiin mee gaeni nahutetta ddolar valin puravalaa nattavannee lankaavatta tiyunu vidihatta pahara gahanna....  gaenigee niyama vansaya nam sinhala baudda venna baehae ...'osariya' boru kavar ekak venna puluvan... sinhala uccaaranaya baeri mokada 'maenikeetta'?

---

### 23. `sold_2299` (label: NOT)

**Sinhala:** ඔව් බං මේ ආත්මේ වගේ නාකි වෙනකං බලං ඉන්න බෑ ඒකිව හම්බෙන්න. ගැටවර වියේදිම මගේ වෙන්න ඕනි URL

- **Phonetic (baseline):** ow ban mee aathmee wagee naaki wenakan balan inna baae eekiwa hambenna. gaetawara wiyeedima magee wenna ooni URL
- **Aksharamukha:** ow ban mee aatmee wagee naaki wenakan balan inna baae eekiwa hambenna. gaetawara wiyeedima magee wenna ooni URL
- **Sinhala G2P (phonemic, retains ə):** ow bang mee aatmee wagee naaki wenəkang balang innə baae eekiwə hambennə. gaetəwərə wiyeedimə magee wennə ooni URL
- **Sinhala G2P (ASCII, ə→a):** ow bang mee aatmee wagee naaki wenakang balang inna baae eekiwa hambenna. gaetawara wiyeedima magee wenna ooni URL
- **uroman:** ov ban mee aatmee vagee naaki venakan balan inna bae eekiva hambenna. gaettavara viyeedima magee venna ooni URL

---

### 24. `sold_2414` (label: NOT)

**Sinhala:** @USER ඊයා යකෝ දැන්ද බ්ලොක් වුනේ

- **Phonetic (baseline):** @USER iiyaa yakoo daenda blok wunee
- **Aksharamukha:** @USER iiyaa yakoo daenda blok wunee
- **Sinhala G2P (phonemic, retains ə):** @USER iiyaa yakoo daendə blok wunee
- **Sinhala G2P (ASCII, ə→a):** @USER iiyaa yakoo daenda blok wunee
- **uroman:** @USER iiyaa yakoo daenda blok vunee

---

### 25. `sold_2473` (label: NOT)

**Sinhala:** අයිසෙ වෙලාව,   වෙයන්කො ඉක්මණට වැඩ තියෙනව

- **Phonetic (baseline):** ayise welaawa,   weyanko ikmanata waeda thiyenawa
- **Aksharamukha:** ayise welaawa,   weyanko ikmanata waeda tiyenawa
- **Sinhala G2P (phonemic, retains ə):** aise welaawə,   weyanko ikmənətə waedə tiyenəwə
- **Sinhala G2P (ASCII, ə→a):** aise welaawa,   weyanko ikmanata waeda tiyenawa
- **uroman:** ayise velaava,   veyanko ikmanatta vaedda tiyenava

---
