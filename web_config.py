import streamlit as st
from jinja2 import Template

# Template Jinja2 
template_string = """
interface {{ interface_name }}
 vlan-type dot1q {{ vlan_id }}
 description {{ description }}
 ipv6 enable
 ip address {{ ip_pe }} {{ ip_mask }}
 ipv6 address {{ ipv6_pe }}/{{ ipv6_prefix }}
 statistic enable
 qos car cir {{ bandwidth }} pir {{ bandwidth }} inbound
 qos car cir {{ bandwidth }} pir {{ bandwidth }} outbound
#

{% if community_list is defined and community_list|length > 0 %}
xpl community-list {{ customer_name }}_AS{{ asn }}
{% for comm in community_list %}
 {{ comm }}{% if not loop.last %},{% endif %}
{% endfor %}
 end-list
#
{% endif %}

xpl ip-prefix-list {{ customer_name }}_AS{{ asn }}
{% for prefix in ipv4_prefixes %}
{{ prefix }}{% if not loop.last %},{% endif %}
{% endfor %}
end-list
#
xpl ipv6-prefix-list {{ customer_name }}_AS{{ asn }}_IPV6
{% for prefix in ipv6_prefixes %}
{{ prefix }}{% if not loop.last %},{% endif %}
{% endfor %}
end-list
#
xpl route-filter rp_{{ customer_name|lower }}_as{{ asn }}_in
 if ip route-destination in DENY_GOOGLE or ip route-destination in DENY_CLOUDFLARE then
  refuse
 elseif ip route-destination in {0.0.0.0 0 ge 32 le 32} then
  apply community rtbh additive
  apply ip next-hop blackhole
 elseif ip route-destination in rfc1918_match_prefix then
  refuse
 elseif as-path in {regular ^{{ asn }}_} and ip route-destination in {{ customer_name }}_AS{{ asn }} then
  apply community {{ customer_name }}_AS{{ asn }} additive
  apply local-preference 210
 else
  refuse
 endif
 end-filter
#
xpl route-filter {{ customer_name }}_AS{{ asn }}_IN
 call route-filter rp_{{ customer_name|lower }}_as{{ asn }}_in
 end-filter
#
xpl route-filter {{ customer_name }}_AS{{ asn }}_IPV6_IN
 if ipv6 route-destination in {{ customer_name }}_AS{{ asn }}_IPV6 then
  apply community {{ customer_name }}_AS{{ asn }} additive
  apply local-preference 210
 endif
 end-filter
#
xpl route-filter rp_{{ customer_name|lower }}_as{{ asn }}_out
 if ip route-destination in {0.0.0.0 0} and ipv6 route-destination in NULL then
  refuse
 elseif ip route-destination in rfc1918_match_prefix and ipv6 route-destination in NULL then
  refuse
 elseif ip route-destination in localIP and ipv6 route-destination in NULL then
  apply med 0
 elseif ipv6 route-destination in localIP and ip route-destination in NULL then
  apply med 0
 elseif community matches-any allCustomer then
  apply med 0
 endif
 end-filter
#
xpl route-filter {{ customer_name }}_AS{{ asn }}_OUT
 call route-filter rp_allUpstream
 call route-filter rp_{{ customer_name|lower }}_as{{ asn }}_out
 end-filter
#
bgp {{ local_asn }}
 peer {{ ip_ce }} as-number {{ asn }}
 peer {{ ip_ce }} group external
 peer {{ ip_ce }} description {{ customer_name }}_AS{{ asn }}
 peer {{ ipv6_ce }} as-number {{ asn }}
 peer {{ ipv6_ce }} group external
 peer {{ ipv6_ce }} description {{ customer_name }}_AS{{ asn }}
 ipv4-family unicast
  peer {{ ip_ce }} enable
  peer {{ ip_ce }} group external
  peer {{ ip_ce }} route-filter {{ customer_name }}_AS{{ asn }}_IN import
  peer {{ ip_ce }} route-filter {{ customer_name }}_AS{{ asn }}_OUT export
  peer {{ ip_ce }} route-limit accept-prefix 100 90 idle-timeout 10
  peer {{ ip_ce }} advertise-community
  peer {{ ip_ce }} keep-all-routes
 ipv6-family unicast
  peer {{ ipv6_ce }} enable
  yes
  peer {{ ipv6_ce }} route-filter {{ customer_name }}_AS{{ asn }}_IPV6_IN import
  peer {{ ipv6_ce }} route-limit accept-prefix 100 90 idle-timeout 10
  peer {{ ipv6_ce }} keep-all-routes
"""

# Pengaturan Halaman Web
st.set_page_config(page_title="Generator Config NAP", layout="wide")
st.title("🌐 Generator Aktivasi User IPT")
st.markdown("---")

# Membagi layar menjadi 2 kolom (Kiri: Form, Kanan: Hasil)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 1. Form Input Data")
    
    customer_name = st.text_input("1. Nama Customer (format: NAMA_CUSTOMER):")
    asn = st.text_input("2. AS Number Customer:")
    interface_name = st.text_input("3. Interface (contoh: eth-trunk0.xxx):")
    vlan_id = st.text_input("4. VLAN ID:")
    description = st.text_input("5. Description Interface (Kosongkan utk default):", help="Format: CRTXXXX-IPT-NAMA_CUSTOMER-AS_NUMBER-SITE")
    
    ip_pe = st.text_input("6. IP P2P NAP /31 (contoh: 123.176.123.254):")
    ip_ce = st.text_input("7. IP P2P User /31 (contoh: 123.176.123.255):")
    ipv6_pe = st.text_input("8. IPv6 P2P NAP /127 (contoh: 2400:D740::123:176:123:254):")
    ipv6_ce = st.text_input("9. IPv6 P2P User /127 (contoh: 2400:D740::123:176:123:255):")
    bandwidth = st.text_input("10. Bandwidth dlm Kbps (contoh: 1024000000):")

    st.info("Masukkan Prefix (Satu baris per prefix)")
    ipv4_text = st.text_area("-> IPv4 Prefix (contoh: xxx.xxx.xxx.0 24):", height=100)
    ipv6_text = st.text_area("-> IPv6 Prefix (contoh: xxxx:xxxx:xxxx:: /32):", height=100)

    # Tombol Generate
    generate = st.button("🚀 GENERATE CONFIGURASI", type="primary", use_container_width=True)

with col2:
    st.subheader("💻 2. Hasil Konfigurasi")
    
    if generate:
        if not customer_name or not asn:
            st.error("Nama Customer dan AS Number wajib diisi!")
        else:
            # Validasi deskripsi
            if not description:
                description = f"CRTXXXX-IPT-{customer_name}-AS{asn}-JKT"
            
            # Pembersihan IP
            ip_pe_clean = ip_pe.split('/')[0].strip() if ip_pe else ""
            ip_ce_clean = ip_ce.split('/')[0].strip() if ip_ce else ""
            ipv6_pe_clean = ipv6_pe.split('/')[0].strip() if ipv6_pe else ""
            ipv6_ce_clean = ipv6_ce.split('/')[0].strip() if ipv6_ce else ""

            ipv4_prefixes = [p.strip() for p in ipv4_text.split('\n') if p.strip()]
            ipv6_prefixes = [p.strip() for p in ipv6_text.split('\n') if p.strip()]

            # Gabungkan ke dictionary
            customer_data = {
                "interface_name": interface_name,
                "vlan_id": vlan_id,
                "description": description,
                "ip_pe": ip_pe_clean,
                "ip_mask": "255.255.255.254", 
                "ip_ce": ip_ce_clean,
                "ipv6_pe": ipv6_pe_clean,
                "ipv6_prefix": "127",         
                "ipv6_ce": ipv6_ce_clean,
                "bandwidth": bandwidth,
                "customer_name": customer_name,
                "asn": asn,
                "local_asn": "136106",        
                "community_list": ["13610:50000", "13610:63000", "13610:64000"],
                "ipv4_prefixes": ipv4_prefixes,
                "ipv6_prefixes": ipv6_prefixes
            }

            try:
                # Proses Jinja2
                template = Template(template_string)
                generated_config = template.render(customer_data)
                
                st.success(f"Konfigurasi untuk {customer_name} berhasil dibuat!")
                
                # Tampilkan hasil di box code
                st.code(generated_config, language='text')
                
                # Tambahkan tombol Download File
                file_name = f"{customer_name}_AS{asn}.txt"
                st.download_button(
                    label="📥 Download File .txt",
                    data=generated_config,
                    file_name=file_name,
                    mime="text/plain",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
