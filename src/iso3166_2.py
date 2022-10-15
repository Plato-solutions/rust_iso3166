#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import csv

pre_code = """
use phf::phf_map;
use phf::Map;

#[cfg(feature = "with-serde")]
use serde::{Serialize,ser::{Serializer,SerializeStruct},de::{self, Deserialize, Deserializer, Visitor, SeqAccess, MapAccess}};

#[cfg(feature = "with-serde")]
use std::fmt;

#[cfg(feature = "with-schemars")]
use schemars::JsonSchema;

/// # Sample code
/// ```
/// let country = rust_iso3166::from_alpha2("GB").unwrap();
/// let subdivisions = country.subdivisions();
/// assert!(subdivisions.unwrap().len() > 0);
/// let country = rust_iso3166::iso3166_2::from_code("GB-EDH");
/// assert_eq!("Edinburgh, City of", country.unwrap().name); 
/// println!("{:?}", rust_iso3166::iso3166_2::SUBDIVISION_COUNTRY_MAP); 
/// println!("{:?}", rust_iso3166::iso3166_2::SUBDIVISION_MAP); 
/// ```
///
/// Data for each Country Code defined by ISO 3166-2
#[cfg_attr(feature = "with-schemars", derive(JsonSchema))]
#[cfg_attr(feature = "with-eq", derive(PartialEq,Eq))] //@TODO more efficient implementation possible
#[derive(Debug, Copy, Clone)]
pub struct Subdivision {
    ///name
    pub name: &'static str,
    ///type
    pub subdivision_type: &'static str,
    ///code
    pub code: &'static str,
    ///Country Name
    pub country_name: &'static str,
    ///Country Code
    pub country_code: &'static str,
    ///Region Code
    pub region_code: &'static str,
}

/// Returns the Subdivision with the given code, if exists.
/// #Sample
/// ```
/// let sub = rust_iso3166::iso3166_2::from_code("SE-O");
/// assert_eq!("Västra Götalands län", sub.unwrap().name);
/// ```
pub fn from_code(code: &str) -> Option<Subdivision> {
    SUBDIVISION_MAP.get(code).cloned()
}

#[cfg(feature = "with-serde")]
impl Serialize for Subdivision {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
        where
            S: Serializer,
    {
        let mut state = serializer.serialize_struct("Subdivision", 1)?;
        state.serialize_field("region_code", &self.region_code)?;
        state.end()
    }
}

#[cfg(feature = "with-serde")]
impl<'de> Deserialize<'de> for Subdivision {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
        where
            D: Deserializer<'de>,
    {
        enum Field { RegionCode }
        
        impl<'de> Deserialize<'de> for Field {
            fn deserialize<D>(deserializer: D) -> Result<Field, D::Error>
                where
                    D: Deserializer<'de>,
            {
                struct FieldVisitor;

                impl<'de> Visitor<'de> for FieldVisitor {
                    type Value = Field;

                    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                        formatter.write_str("`region_code`")
                    }

                    fn visit_str<E>(self, value: &str) -> Result<Field, E>
                        where
                            E: de::Error,
                    {
                        match value {
                            "region_code" => Ok(Field::RegionCode),
                            _ => Err(de::Error::unknown_field(value, FIELDS)),
                        }
                    }
                }

                deserializer.deserialize_identifier(FieldVisitor)
            }
        }

        struct SubdivisionVisitor;

        impl<'de> Visitor<'de> for SubdivisionVisitor {
            type Value = Subdivision;

            fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
                formatter.write_str("struct Subdivision")
            }

            fn visit_seq<V>(self, mut seq: V) -> Result<Subdivision, V::Error>
                where
                    V: SeqAccess<'de>,
            {
                let region_code = seq.next_element()?
                    .ok_or_else(|| de::Error::invalid_length(0, &self))?;
                Ok(from_code(region_code).expect(format!("deserialized Subdivision region_code({}) not found",region_code).as_str()))
            }

            fn visit_map<V>(self, mut map: V) -> Result<Subdivision, V::Error>
                where
                    V: MapAccess<'de>,
            {
                let mut region_code = None;
                while let Some(key) = map.next_key()? {
                    match key {
                        Field::RegionCode => {
                            if region_code.is_some() {
                                return Err(de::Error::duplicate_field("region_code"));
                            }
                            region_code = Some(map.next_value()?);
                        }
                    }
                }
                let region_code = region_code.ok_or_else(|| de::Error::missing_field("region_code"))?;
                Ok(from_code(region_code).expect(format!("deserialized Subdivision region_code({}) not found",region_code).as_str()))
            }
        }


        const FIELDS: &'static [&'static str] = &["region_code"];
        deserializer.deserialize_struct("Subdivision", FIELDS, SubdivisionVisitor)
    }
}

"""
print pre_code
f =  csv.reader(open('iso3166_2.data', 'rb'), delimiter=',', quotechar='"')
subdivisions = {}
for x in f:
    

    ts1 = x[1].split("-")
     
    region_code = x[1]
    country_code = x[4]
    country_name = x[0]
    sub_name = x[2]
    sub_code = x[1]
    sub_type = x[3]
    var_name = sub_code.replace("-","_")

    if not country_code in subdivisions:
        subdivisions[country_code] = []
    subdivisions[country_code].append({
        "name":sub_name,
        "var_name": var_name,
        "code":sub_code,
        "type":sub_type,
        "country_name":country_name,
        "country_code":country_code,
        "region_code":region_code,
    })
    print """
pub const %s: Subdivision = Subdivision {
    name: "%s",
    code: "%s",
    subdivision_type: "%s",
    country_name: "%s",
    country_code: "%s",
    region_code: "%s",
};
""" % (var_name,sub_name,sub_code,sub_type,country_name,country_code,region_code)
    

print """
///Subdivision map with  Code key 
pub const SUBDIVISION_MAP: Map<&str, Subdivision> = phf_map! {
"""
for key in subdivisions:
    for sub in subdivisions[key]:
        print "\"%s\" => %s," % (sub["code"],sub["var_name"])
print """
};
"""

print """
///Subdivision map with  Code key 
pub const SUBDIVISION_COUNTRY_MAP: Map<&str, &[Subdivision]> = phf_map! {
"""
for key in subdivisions:
    print "\"%s\" => &[" % (key) 
    for sub in subdivisions[key]:
        print "%s," % (sub["var_name"])
    print "]," 
print """
};
"""