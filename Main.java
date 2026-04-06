package app;

import java.util.*;

public class Main {

    public static void main(String[] args) {

        ScraperKos scraper = new ScraperKos();

        List<Kos> hasil = scraper.scrape();

        for(Kos k : hasil){
            k.tampil();
        }

    }
}