import datetime as dt
import pandas as pd

# Veriyi Anlama ve Hazırlama
df_ = pd.read_csv("flo_data_20k.csv")
df = df_.copy()


def check_df(dataframe, head=5, quantiles=(0, 0.05, 0.50, 0.95, 0.99, 1)):
    print("##################### Shape #####################")
    print(dataframe.shape)
    print("##################### Types #####################")
    print(dataframe.dtypes)
    print("##################### Head #####################")
    print(dataframe.head(head))
    print("##################### Tail #####################")
    print(dataframe.tail(head))
    print("##################### NA #####################")
    print(dataframe.isnull().sum())
    print("##################### Index ####################")
    print(dataframe.index)
    print("##################### Quantiles #####################")
    print(dataframe.describe(list(quantiles)).T)


check_df(df)

# Tarih belirten object değişkenlerin tipini datetime64[ns]'e dönüştürme.
for column in df.columns[3:7]:
    df[column] = pd.to_datetime(df[column])

# RFM metriklerini tanımlama
today_date = dt.datetime(2021, 6, 1)

rfm = pd.DataFrame({"master_id": df["master_id"],
                    "recency": df["last_order_date"].apply(lambda x: (today_date - x).days),
                    "frequency": df['order_num_total_ever_online'] + df['order_num_total_ever_offline'],
                    "monetary": df['customer_value_total_ever_offline'] + df['customer_value_total_ever_online']})

# RF Skorunun Hazırlanması
rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
rfm["monetary_score"] = pd.qcut(rfm['monetary'].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

rfm["RF_SCORE"] = rfm['recency_score'].astype(str) + rfm['frequency_score'].astype(str)

# RF Skorunun Segment Olarak Tanımlanması
seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

rfm["segment"] = rfm["RF_SCORE"].replace(seg_map, regex=True)

# Örnekler

# a.FLO bünyesine yeni bir kadın ayakkabı markası dahil ediyor. Dahil ettiği markanın ürün fiyatları genel müşteri
# tercihlerinin üstünde. Bu nedenle markanın tanıtımı ve ürün satışları için ilgilenecek profildeki müşterilerle
# özel olarak iletişime geçmek isteniliyor. Sadık müşterilerinden(champions,loyal_customers) ve kadın kategorisinden
# alışveriş yapan kişiler özel olarak iletişim kurulacak müşteriler.
# Bu müşterilerinin numaralarını csv dosyasına kaydediniz.

filtered_indexes = [i for i in df.index if (rfm.loc[i, "monetary"] > rfm["monetary"].quantile(0.75))
                    & ("KADIN" in df.loc[i, "interested_in_categories_12"])
                    & (rfm.loc[i, "segment"] in ["champions", "loyal_customers"])]

filtered_customers = rfm.loc[filtered_indexes, "master_id"]

filtered_customers.to_csv("rfm_case1.csv")

# b.Erkek ve Çocuk ürünlerinde %40'a yakın indirim planlanmaktadır. Bu indirimle ilgili kategorilerle ilgilenen
# geçmişte iyi müşteri olan ama uzun süredir alışveriş yapmayan kaybedilmemesi gereken müşteriler,
# uykuda olanlar ve yeni gelen müşteriler özel olarak hedef alınmak isteniyor. Uygun profildeki müşterilerin id'lerini
# csv dosyasına kaydediniz.

filtered_indexes2 = [i for i in df.index if (("ERKEK" in df.loc[i, "interested_in_categories_12"]) |
                                             ("COCUK" in df.loc[i, "interested_in_categories_12"]))
                     & (rfm.loc[i, "segment"] in ['cant_loose', 'hibernating', 'new_customers'])]

filtered_customers2 = rfm.loc[filtered_indexes2, "master_id"]
filtered_customers2.to_csv("rfm_case2.csv")


