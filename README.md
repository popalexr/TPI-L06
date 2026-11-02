# Laborator 05 - API pentru senzori IoT

In acest laborator am completat fisierul `hello.py` pentru a primi si afisa citiri de la senzori IoT. Am folosit FastAPI pentru API si Pydantic pentru validarea datelor. Citirile sunt pastrate intr-un dictionar in memorie, deci se pierd la oprirea serverului.

Fiecare citire contine numele dispozitivului, numarul de ordine, timpul masurarii, temperatura si, optional, umiditatea. Modelul verifica formatul numelui, numarul de ordine pozitiv sau zero, temperatura intre -40 si 85 de grade si umiditatea intre 0 si 100%. Timpul trebuie sa fie mai mare decat 1600000000, pentru a evita valori trimise de un senzor cu ceasul nesetat.

Am adaugat `POST /readings` pentru salvarea citirilor. La salvare se returneaza codul 201. Daca acelasi dispozitiv trimite din nou un numar de ordine deja salvat, se returneaza 409.

Prin `GET /devices/{dev_id}/readings` se pot vedea citirile unui dispozitiv. Parametrul `since` pastreaza doar citirile cu numar de ordine mai mare, iar `limit` stabileste cate rezultate sunt afisate. Rezultatele sunt ordonate crescator dupa numarul de ordine. Pentru un dispozitiv fara citiri se returneaza 404, iar pentru date sau parametri invalizi se returneaza automat 422.

Am facut si bonusurile: filtrul `min_temp`, care pastreaza temperaturile cel putin egale cu valoarea ceruta, si `GET /devices`, care afiseaza dispozitivele si numarul de citiri pentru fiecare.

In `test_hello.py` am scris teste cu pytest si TestClient pentru cele 11 cazuri din cerinta, bonusuri si cateva verificari suplimentare. Toate cele 23 de teste au trecut.

Serverul se porneste cu `fastapi dev hello.py`, iar cererile pot fi incercate la `http://127.0.0.1:8000/docs`. Testele se ruleaza cu `.venv/bin/python -m pytest -q`.
