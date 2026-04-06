package app;

import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import java.util.*;

public class Scraping {

    public List<Kos> scrape() {

        List<Kos> listKos = new ArrayList<>();

        System.setProperty("webdriver.chrome.driver", "chromedriver.exe");

        WebDriver driver = new ChromeDriver();
        driver.get("https://mamikos.com");

        try {
            Thread.sleep(5000);
        } catch (Exception e) {}

        List<WebElement> nama = driver.findElements(By.className("rc-info__name"));
        List<WebElement> lokasi = driver.findElements(By.className("rc-info__location"));
        List<WebElement> harga = driver.findElements(By.className("kost-rc__price"));

        for(int i=0; i<nama.size(); i++){

            Kos kos = new Kos(
                nama.get(i).getText(),
                lokasi.get(i).getText(),
                harga.get(i).getText()
            );

            listKos.add(kos);
        }

        driver.quit();

        return listKos;
    }
}