# Boprisindikatorn: teknisk rapport

## Bakgrund och syfte

I Boprisindikatorn har vi byggt en applikation som uppskattar utgångspriset för lägenheter, villor och radhus med hjälp av maskininlärning. Projektet omfattar hela flödet från bostadsdata och modellträning till en app där användaren kan göra en uppskattning och utforska resultaten. Vi ville också undersöka vilka uppgifter om en bostad som hjälper modellen att göra bättre uppskattningar.

Vi märkte tidigt att den största utmaningen låg i att förstå och förbereda datan. Rådatasetet innehåller 11 549 bostadsannonser och uppgifter om bland annat utgångspris, bostadstyp, boarea, antal rum, adress och koordinater. Det saknar däremot flera faktorer som kan påverka priset. Vi behövde därför vara tydliga med vilka bostäder modellen skulle gälla för, hur osäkra värden skulle hanteras och vad resultatet faktiskt betyder. Modellen uppskattar **utgångspris**, inte slutpris vid försäljning.

## Från rådata till jämförbara modeller

Vi behöll de tre bostadstyper som appen stödjer och tog bort objekt med bland annat ogiltigt pris, saknad boarea eller orimliga koordinater. Vi satte också gränser för storlek och antal rum per bostadstyp samt avgränsade utgångspriset till 100 000–10 000 000 kronor. För lägenheter används ingen tomtarea. Osäkra små tomtareor för villor behandlades som saknade värden. Dessa val minskade antalet bostäder i träningen, men gjorde det tydligare vilken sorts objekt modellen faktiskt är avsedd för. Råfilen lämnades orörd och den tvättade datan sparades separat.

En stor del av tiden gick åt till att bygga om notebooken för modellträning. Vi ville kunna följa samma ordning varje gång: tvätta data, dela upp den, förbereda variabler, jämföra modeller, välja modell och till sist testa den. Datan delades upp i 60 procent träning, 20 procent validering och 20 procent test. Fördelningen av bostadstyper behölls i varje del. Testdatan användes först efter att modellvalet var gjort, så att den kunde ge en mer rättvis slutkontroll.

Som första jämförelse använde vi en enkel baslinje som alltid gissar medianpriset. Därefter jämförde vi Ridge, Random Forest, Extra Trees och HistGradientBoosting. Vi tränade dels en global modell för alla tre bostadstyperna, dels separata modeller för lägenheter, villor och radhus. Det gjorde att vi kunde undersöka om en modell som bara ser en bostadstyp blir bättre än en som får lära sig av alla objekt. För att jämförelsen skulle vara rättvis mätte vi också globalmodellen och respektive specialmodell på samma testbostäder. Vi valde efter lägst RMSE på valideringsdata och justerade sedan utvalda modeller. En justering behölls bara om den förbättrade valideringsresultatet.

Det här arbetet tog längre tid än vi först trodde. Att få ett lågt RMSE handlade inte bara om att byta algoritm. Vi behövde förstå datasetet, bestämma rimliga urval, skilja på träningsdata och testdata och se till att alla modeller jämfördes med samma mått. Vi följde även MAE, medianfel och R² för att inte låta ett enda tal beskriva hela resultatet. Variabeln pris per kvadratmeter i rådata användes inte som indata, eftersom den redan bygger på det utgångspris vi vill förutsäga.

## Resultat och applikation

Ett av våra tydligaste experiment gällde geografi. Vi jämförde samma modelltyp på samma testbostäder, först utan och sedan med kommun, latitud och longitud. RMSE sjönk från cirka **1 604 000 kronor till 915 000 kronor**, en förbättring på ungefär **43 procent** på 2 018 testbostäder. Förbättringen syntes för lägenheter, villor och radhus. Vi undersökte också boarea i ett eget experiment: med boarea sjönk testresultatets RMSE från cirka **962 000 till 927 000 kronor** jämfört med en annars likadan modell utan boarea. Resultaten visar att plats och storlek hjälper i dessa jämförelser. De visar inte att variablerna ensamma orsakar prisskillnaderna.

Den färdiga applikationen är byggd i Streamlit. Användaren kan ange bostadsuppgifter, få en prisuppskattning och undersöka geografiska mönster, boarea och statistik på separata sidor. De tränade modellerna sparas med både förbehandling och information om träning och testresultat. Appen kan därmed läsa in en färdig modell utan att träna om den vid varje start. SQLite används för att spara gjorda prisuppskattningar med tillhörande uppgifter. Kod och analys delas via Git och GitHub, vilket gör det möjligt att följa arbetet och köra projektet vidare.

## Begränsningar och möjliga förbättringar

Det största utrymmet för att förbättra modellen ligger troligen i uppgifter som datasetet saknar. Två bostäder med samma storlek och i samma område kan ha olika utgångspris därför att deras skick skiljer sig åt. Ett nästa steg vore att komplettera annonserna med uppgifter om renovering, byggår och standard. För lägenheter skulle även månadsavgiften vara särskilt intressant. Dessa uppgifter beskriver skillnader mellan enskilda bostäder som kommun och koordinater inte fullt ut kan fånga.

Vi skulle också kunna slå samman datan med mer detaljerade uppgifter om närområdet, exempelvis avstånd till kollektivtrafik eller vatten. Här räcker det inte att bara lägga till fler kolumner. För varje ny uppgift skulle vi träna två i övrigt likadana modeller, en med och en utan uppgiften, och jämföra dem på samma avskilda data. På så sätt kan vi pröva hypotesen att exempelvis månadsavgift eller närhet till en station faktiskt sänker RMSE. Publiceringsdatum finns redan i rådata och skulle kunna testas på samma sätt för att se om det fångar förändringar över tid. Vi har inte genomfört dessa försök och kan därför inte ange hur stora förbättringarna skulle bli.

Det finns också en begränsning i hur vi mätte felet. Träning och test delades slumpmässigt, vilket innebär att båda delarna kan innehålla bostäder från samma närområde. Ett extra test där hela områden hålls utanför träningen skulle visa hur väl modellen fungerar på platser den inte har sett tidigare. Ett annat framtida projekt vore att förutsäga faktiska slutpriser i stället för utgångspriser, men det kräver ett annat dataset och en ny utvärdering.

## Utvärdering av arbetet

Projektets viktigaste lärdom är hur mycket modellens resultat beror på arbetet före själva träningen. När vi strukturerade om notebooken blev det lättare att se vilka beslut som påverkade resultatet och att jämföra modeller utan att blanda in testdatan för tidigt. De separata hypotesanalyserna hjälpte oss att undersöka en fråga i taget, samtidigt som Git och GitHub gav oss en gemensam plats för kod och ändringar.

Om vi gjorde om projektet skulle vi tidigare fastställa gemensamma regler för datatvätt, modelljämförelse och vilka filer som ska användas i appen. Det hade minskat behovet av att bygga om träningsflödet under arbetets gång. Vi skulle också lägga mer tid på att hitta kompletterande uppgifter om de enskilda bostäderna. Projektet visar att vi fick ett fungerande flöde från data till app, men också att ett mer komplett underlag behövs för säkrare prisuppskattningar.
