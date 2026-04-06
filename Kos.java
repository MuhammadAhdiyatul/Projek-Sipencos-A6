package app;

public class Kos {

    private String Nama;
    private String Lokasi;
    private String Harga;

    public Kos(String Nama, String Lokasi, String Harga) {
        this.nama = Nama;
        this.lokasi = Lokasi;
        this.harga = Harga;
    }

    public String getNama() {
        return Nama;
    }

    public String getLokasi() {
        return Lokasi;
    }

    public String getHarga() {
        return Harga;
    }

    public void tampil() {
        System.out.println(Nama + " | " + Lokasi + " | " + Harga);
    }
}