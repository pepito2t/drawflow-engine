use std::collections::{HashSet, VecDeque};

/// Insertion-ordered set that forgets its oldest entries past a capacity, so a long session
/// never grows without bound and a cleanup never forgets everything at once.
pub struct BoundedSet {
    capacity: usize,
    order: VecDeque<String>,
    members: HashSet<String>,
}

impl BoundedSet {
    pub fn new(capacity: usize) -> Self {
        Self {
            capacity,
            order: VecDeque::new(),
            members: HashSet::new(),
        }
    }

    /// Returns true when the value was not present yet.
    pub fn insert(&mut self, value: String) -> bool {
        if !self.members.insert(value.clone()) {
            return false;
        }
        self.order.push_back(value);
        while self.order.len() > self.capacity {
            if let Some(oldest) = self.order.pop_front() {
                self.members.remove(&oldest);
            }
        }
        true
    }

    pub fn extend<I: IntoIterator<Item = String>>(&mut self, values: I) {
        for value in values {
            self.insert(value);
        }
    }

    pub fn contains(&self, value: &str) -> bool {
        self.members.contains(value)
    }

    /// Oldest first, so a persisted snapshot reloads in the same order.
    pub fn iter(&self) -> impl Iterator<Item = &String> {
        self.order.iter()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn forgets_the_oldest_entries_only() {
        let mut set = BoundedSet::new(3);
        for value in ["a", "b", "c", "d"] {
            assert!(set.insert(value.to_owned()));
        }
        assert!(!set.contains("a"));
        assert!(set.contains("b") && set.contains("c") && set.contains("d"));
        assert!(!set.insert("d".to_owned()));
        assert_eq!(set.iter().cloned().collect::<Vec<_>>(), ["b", "c", "d"]);
    }
}
