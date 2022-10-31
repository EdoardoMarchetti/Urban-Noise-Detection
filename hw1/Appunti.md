# APPUNTI

## STFT

STFT -> (# frqeuency bins, # frames)

* frequency bins = frame_size/2 + 1
* #frames = (samples - framesize / hopsize) + 1

NB: la funzione stft di tensorflow sembra restituire valori diversi da quelli che ci si aspetta dall formule riportate

### Time/Frequency trade off

Aumentando la frame size, vengono analizzati un maggior numero di sample per ogni frame. Ciò comporta che:

* Il numero di frequency bins cresce => maggiore risoluzione in termini di frequenza
* Diminusce la time resolution

Il tradeoff solitamente viene trovato in maniera euristica

## MEL-Spectogram

Gli umani percepiscono le frequenze in maniera logaritmica. Dunque se prendiamo due coppie di frequenze equidistanti, per esempio 400Hz-600Hz e 2400Hz-2600Hz, le seconde sembreranno molto più simili tra loro all'orecchio umano.

Mel (Mel = Melody) è una scala logaritmica usata per rappresentare le frequenze. (1000Hz = 1000Mel)

Come converitre Hz in Mel? => m = 2595 * log(1+ f/500)
Come converitre Mel in Hz? => f = 700(10^(m/2595)-1)

Come ottenere lo spettrogramma in Mel?

1. Estrai STFT
2. Converti l'ampiezza in DBs (decibel)
3. Converti le frequenze nella scala di Mel:
   1. Scegli il numero di bande di mel
   2. Costruisci i mel filter banks
   3. Applica i mel filter banks allo spettrogramma => STFT * MEL_Banks

Come scegliere il numero di bande di mel? Dipende strettamente dal problema (necessità di tuning)

Come costruire i mel filter banks?

1. Converti la frequenza più bassa e più alta da Hz a Mel, di seguito indicate con f_mel e F_mel
2. Crea un numero di punti pari al numero di mel bands equispaziati in [f_mel,F_mel]
3. Converti i punti trovati in 2. in Hz
4. Arrotonda i punti al frequency bin più vicino
5. Crea filtri triangolari


## MFCCs

Mel-Frequency -> utilizzo della scala mel
Cepstral -> Cepstrum -> Spectrum
Coefficients -> valori che descrivono parti dell'audio

Cepstrum -> F^{-1}[log(F[x(t)])]
Cosa si ottiene sull'asse delle x se applichiamo l'inversa della trasformata di fourier ad un segnale nel dominio della frequenza? Quefrency

1st Rhamonic? Quefrency associata alla frequenza portante

