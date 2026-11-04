# Pracownia publikacji RPG — lokalny edytor

**Nie musisz ręcznie edytować HTML ani JavaScriptu.** Edytor pracuje na plikach Twojej statycznej strony i nie wysyła danych do Internetu.

## Uruchomienie

1. Zainstaluj **Python 3.10 lub nowszy** (jeżeli go nie masz). Żadne pakiety `pip` nie są potrzebne.
2. Rozpakuj ZIP w folderze projektu strony (tam, gdzie jest `index.html`).
3. **Windows:** dwukrotnie kliknij `start-edytor.bat` (albo `py -3 edytor.py` w terminalu).
   **macOS/Linux:** uruchom `./start-edytor.sh` (albo `python3 edytor.py`).
4. Otworzy się przeglądarka z lokalnym panelem. Jeżeli nie otworzy się sama, skopiuj do niej adres `http://127.0.0.1:PORT/` wypisany w terminalu.
5. Aby zamknąć edytor, użyj `Ctrl+C` w terminalu.

**Ważne:** uruchamiaj aplikację z folderu swojej strony. Jeżeli repozytorium GitHub ma inny folder niż rozpakowany ZIP, skopiuj zawartość do repozytorium i uruchamiaj stamtąd — inaczej zmiany będą zapisywane w niewłaściwej kopii.

## Publikowanie artykułu

1. Kliknij **Nowy artykuł** i wpisz tytuł, kategorię, zajawkę oraz pełny tekst.
2. Formatuj artykuł przyciskami albo przez Markdown: `## Nagłówek`, `**pogrubienie**`, `*kursywa*`, `- lista`, `> cytat`.
3. Opcjonalnie dodaj zdjęcie. Wprowadź datę.
4. Możesz zapisać **szkic**. Zostanie w lokalnym katalogu `.szkice-lokalne/`, który jest ignorowany przez Git i **nie będzie publikowany**.
5. Kiedy artykuł jest gotowy, kliknij **Opublikuj artykuł**. Aplikacja tworzy:
   - `content/articles/<adres>.json` – treść źródłową, do późniejszej edycji;
   - `wpisy/<adres>.html` – stronę artykułu;
   - aktualizację `tworczosc-data.js` – karta wpisu na Twojej stronie;
   - jeśli przesłałeś okładkę: plik `images/blog/...`.
6. W folderze repozytorium wykonaj:

```sh
git add .
git commit -m "Nowy artykuł RPG"
git push
```

Po opublikowaniu przez GitHub Pages (jeśli z niego korzystasz) nowy wpis będzie widoczny na stronie. Sam edytor **nigdy nie robi commita ani pusha**.

## Edycja i usuwanie

- Opublikowany artykuł można ponownie otworzyć, zmienić i kliknąć **Zaktualizuj artykuł** lub **Zapisz szkic** – zmiany pozostaną publiczne, ale tylko lokalnie do czasu commita.
- **Wycofaj publikację** przenosi artykuł do lokalnych szkiców i usuwa jego wygenerowany HTML oraz kartę z listy. Aby wycofanie zadziałało na stronie internetowej, zrób commit.
- Lokalne szkice można usunąć w panelu.
- Nie zmieniaj adresu (sluga) opublikowanego wpisu, ponieważ zepsułoby to stare linki.

## Publikacje RPG

W zakładce **Publikacje RPG** możesz wpisać tytuł, system, format, opis, przesłać okładkę i wkleić odnośnik do DriveThruRPG. Program zapisze `content/publications.json` i automatycznie zaktualizuje `tworczosc-data.js`.

## Struktura repozytorium

```text
index.html
... pozostałe podstrony
edytor.py                 # lokalna aplikacja – nie jest uruchamiana na GitHub Pages
editor/                   # interfejs edytora w przeglądarce
artykul.css              # styl pojedynczego artykułu
content/
  articles/               # źródła opublikowanych artykułów
  publications.json       # dane wydanych produktów
  legacy-articles.json    # stare wpisy zaimportowane z JavaScriptu
wpisy/                    # gotowe artykuły HTML
images/blog/              # okładki dodane w edytorze
.szkice-lokalne/          # wyłącznie prywatne szkice (nie publikować)
tworczosc-data.js         # automatyczny indeks artykułów i publikacji
```

## Bezpieczeństwo / ograniczenia

- Serwer działa tylko na `127.0.0.1` i otwiera losowy port. Edytor posiada zabezpieczenie przed żądaniami z innych stron.
- Dodawaj do strony tylko zdjęcia, do których masz prawo użycia.
- Obsługiwany jest prosty Markdown (nagłówki, listy, cytaty, linki, pogrubienie, kursywa, kod). To nie jest edytor pełnego HTML/WYSIWYG.
- Aplikacja korzysta z Pythona dostępnego na komputerze, bez instalacji bibliotek.
- Przy pierwszym uruchomieniu importuje dane z obecnego `tworczosc-data.js`. Zanim zaczniesz, warto zrobić commit lub kopię zapasową repozytorium.
- Jeśli sklonujesz repozytorium na inny komputer, opublikowane wpisy będą dostępne do edycji dzięki plikom `content/articles/*.json`; prywatne szkice pozostają na pierwszym komputerze.
